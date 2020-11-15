export interface ApiObject {
    self: ApiLink;
}

export interface GenericApiObject extends ApiObject {
    [prop: string]: any;
}

export interface ApiLink {
    href: string;
    rel: string[];
    resourceType: string;
    doc?: string;
    schema?: string;
}

export function matchesLinkRel(link: ApiLink, rel: string | string[]): boolean {
    if (typeof rel === "string") {
        return link.rel.some(linkRel => linkRel === rel);
    } else {
        return rel.every(r => {
            return link.rel.some(linkRel => linkRel === r);
        });
    }
}

export interface KeyedApiLink extends ApiLink {
    key: string[];
}

export interface ApiLinkKey {
    [prop: string]: string;
}

export function applyKeyToLinkedKey(keyedLink: KeyedApiLink, key: ApiLinkKey): ApiLink {
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
    // build new api link
    const apiLink: ApiLink = {
        href: url,
        rel: keyedLink.rel,
        resourceType: keyedLink.resourceType,
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

