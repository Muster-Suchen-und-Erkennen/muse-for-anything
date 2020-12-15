export interface ApiObject {
    self: ApiLink;
}

export function isApiObject(obj: any): obj is ApiObject {
    return obj?.self != null && isApiLinkBase(obj?.self);
}

export interface NewApiObject extends ApiObject {
    new: ApiLink;
}

export function isNewApiObject(obj: any): obj is NewApiObject {
    if (!isApiObject(obj)) {
        return false;
    }
    if (obj.self.resourceType !== "new") {
        return false;
    }
    return (obj as NewApiObject)?.new != null && isApiLinkBase((obj as NewApiObject)?.new);
}

export interface ChangedApiObject extends ApiObject {
    changed: ApiLink;
}

export function isChangedApiObject(obj: any): obj is ChangedApiObject {
    if (!isApiObject(obj)) {
        return false;
    }
    if (obj.self.resourceType !== "changed") {
        return false;
    }
    return (obj as ChangedApiObject)?.changed != null && isApiLinkBase((obj as ChangedApiObject)?.changed);
}

export interface GenericApiObject extends ApiObject {
    [prop: string]: any;
}

export interface ApiLinkBase {
    href: string;
    rel: string[];
    resourceType: string;
    doc?: string;
    schema?: string;
}

export function isApiLinkBase(obj: any): obj is ApiLinkBase {
    return obj?.href != null && obj?.rel != null && obj.resourceType != null;
}

export interface ApiLinkKey {
    [prop: string]: string;
}

export interface ApiLink extends ApiLinkBase {
    resourceKey?: ApiLinkKey;
}

export function matchesLinkRel(link: ApiLinkBase, rel: string | string[]): boolean {
    if (typeof rel === "string") {
        return link.rel.some(linkRel => linkRel === rel);
    } else {
        return rel.every(r => {
            return link.rel.some(linkRel => linkRel === r);
        });
    }
}

export interface KeyedApiLink extends ApiLinkBase {
    key: string[];
    queryKey: string[];
}

export function isKeyedApiLink(obj: any): obj is KeyedApiLink {
    return isApiLinkBase(obj) && ((obj as any)?.key != null || (obj as any)?.queryKey != null);
}

export function checkKeyMatchesKeyedLink(key: ApiLinkKey, keyedLink: KeyedApiLink): boolean {
    return keyedLink.key.every(keyVariable => key[keyVariable] != null);
}

export function checkKeyMatchesKeyedLinkExact(key: ApiLinkKey, keyedLink: KeyedApiLink): boolean {
    const allKeysMatch = checkKeyMatchesKeyedLink(key, keyedLink);
    const queryKeys = Object.keys(key).filter(keyVariable => keyVariable.startsWith("?"));
    if (queryKeys.length === 0) {
        return allKeysMatch;
    }
    const allowedQueryKeys = new Set(keyedLink.queryKey?.map(k => `?${k}`) ?? []);
    const allQueryKeysAllowed = queryKeys.every(queryKey => allowedQueryKeys.has(queryKey));
    return allKeysMatch && allQueryKeysAllowed && Object.keys(key).filter(keyVariable => !keyVariable.startsWith("?")).length === keyedLink.key.length;
}

export function applyKeyToLinkedKey(keyedLink: KeyedApiLink, key: ApiLinkKey): ApiLink {
    let url = keyedLink.href;
    const keyVariables = Object.keys(key).filter(keyVariable => !keyVariable.startsWith("?"));
    // check if key matches
    if (!checkKeyMatchesKeyedLink(key, keyedLink)) {
        throw Error(`Cannot apply key ${key} to keyedLink with key ${keyedLink.key}`);
    }
    // apply key to templated url
    keyVariables.forEach(keyVariable => {
        url = url.replace(`{${keyVariable}}`, key[keyVariable]);
    });

    const queryKeyVariables = Object.keys(key).filter(keyVariable => keyVariable.startsWith("?"));
    if (queryKeyVariables.length > 0) {
        const query = queryKeyVariables.map(k => `${k.substring(1)}=${key[k]}`).join("&");
        url += `?${query}`;
    }

    // build new api link
    const apiLink: ApiLink = {
        href: url,
        rel: keyedLink.rel,
        resourceType: keyedLink.resourceType,
        resourceKey: {...key},
    };
    if (keyedLink.doc != null) {
        apiLink.doc = keyedLink.doc;
    }
    if (apiLink.schema != null) {
        apiLink.schema = keyedLink.schema;
    }
    return apiLink;
}

export interface ApiResponse<T> {
    links: ApiLink[];
    embedded?: Array<ApiResponse<unknown>>;
    data: T;
    keyedLinks?: KeyedApiLink[];
    key?: ApiLinkKey;
}

export function isApiResponse(obj: any): obj is ApiResponse<unknown> {
    return obj?.links != null && obj?.data != null && isApiObject(obj.data);
}

