export interface ApiObject {
    self: ApiLink;
}

export interface GenericApiObject extends ApiObject {
    [prop: string]: any;
}

export interface ApiLink {
    href: string;
    rel: string[];
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

export interface KeyedApiLink {
    key: string[];
}

export interface ApiLinkKey {
    [prop: string]: string;
}

export interface ApiResponse<T> {
    links: ApiLink[];
    embedded?: Array<ApiResponse<unknown>>;
    data: T;
    keyedLinks?: KeyedApiLink[];
    key?: ApiLinkKey;
}

