export interface ApiObject {
    self: ApiLink;
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
}

export function checkKeyMatchesKeyedLink(key: ApiLinkKey, keyedLink: KeyedApiLink): boolean {
    return keyedLink.key.every(keyVariable => key[keyVariable] != null);
}

export function checkKeyMatchesKeyedLinkExact(key: ApiLinkKey, keyedLink: KeyedApiLink): boolean {
    return checkKeyMatchesKeyedLink(key, keyedLink) && Object.keys(key).length === keyedLink.key.length;
}

export function applyKeyToLinkedKey(keyedLink: KeyedApiLink, key: ApiLinkKey, queryParams?: ApiLinkKey): ApiLink {
    let url = keyedLink.href;
    const keyVariables = Object.keys(key);
    // check if key matches
    if (!keyVariables.every(keyVariable => keyedLink.key.includes(keyVariable))) {
        throw Error(`Cannot apply key ${keyVariables} to keyedLink with key ${keyedLink.key}`);
    }
    // apply key to templated url
    keyVariables.forEach(keyVariable => {
        url = url.replace(`{${keyVariable}}`, key[keyVariable]);
    });

    if (Object.keys(queryParams).length > 0) {
        const query = Object.keys(queryParams)
            .map(k => `${k}=${queryParams[k]}`)
            .join("&");
        url += `?${query}`;
    }

    const fullKey = {
        ...key,
        ...(queryParams ?? {}),
    };

    // build new api link
    const apiLink: ApiLink = {
        href: url,
        rel: keyedLink.rel,
        resourceType: keyedLink.resourceType,
        resourceKey: fullKey,
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

