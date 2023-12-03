import { EventAggregator } from "aurelia-event-aggregator";
import { HttpClient } from "aurelia-fetch-client";
import { autoinject } from "aurelia-framework";
import { REQUEST_FRESH_LOGIN_CHANNEL, REQUEST_LOGOUT_CHANNEL } from "resources/events";
import { ApiLink, ApiLinkKey, ApiObject, ApiResponse, applyKeyToLinkedKey, checkKeyCompatibleWithKeyedLink, checkKeyMatchesKeyedLink, checkKeyMatchesKeyedLinkExact, GenericApiObject, isApiObject, isApiResponse, isChangedApiObject, isDeletedApiObject, KeyedApiLink, matchesLinkRel } from "./api-objects";

export class ResponseError extends Error {
    readonly status: number;
    readonly response: Response;

    constructor(message: string, response: Response) {
        super(message);
        this.status = response.status;
        this.response = response;
    }
}

@autoinject
export class BaseApiService {
    static API_VERSION = "v0.1";
    static API_ROOT_URL = "./api/";
    static CACHE_VERSION = 1;
    static CURRENT_CACHES = {
        api: `api-cache-v${BaseApiService.CACHE_VERSION}`,
        apiEmbedded: `api-embedded-cache-v${BaseApiService.CACHE_VERSION}`,
    };

    private http: HttpClient;
    private events: EventAggregator;

    private apiRoot: Promise<ApiResponse<GenericApiObject>>;
    private apiCache: Cache;
    private apiEmbeddedCache: Cache;

    private clientUrlToApiLink: Map<string, ApiLink> = new Map();
    private keyedLinksByKey: Map<string, KeyedApiLink> = new Map();
    private keyedLinkyByResourceType: Map<string, KeyedApiLink[]> = new Map();
    private rootNavigationLinks: ApiLink[] = [];

    private _defaultAuthorization: string;

    constructor(http: HttpClient, eventAggregator: EventAggregator) {
        this.http = http;
        this.events = eventAggregator;
    }

    public set defaultAuthorization(authorization: string) {
        this._defaultAuthorization = authorization;
    }

    public resetDefaultAuthorization() {
        this._defaultAuthorization = null;
    }

    private resolveRel(links: ApiLink[], rel: string | string[]): ApiLink {
        const link: ApiLink = links.find(link => matchesLinkRel(link, rel));
        if (link == null) {
            throw Error(`Could not find a link with the relation ${rel}!`);
        }
        return link;
    }

    private keyedLinkToStringKey(keyedLink: KeyedApiLink): string {
        const key = [...keyedLink.key];
        key.sort(); // sort keys consistently
        return `${keyedLink.resourceType}/${key.join("/")}`;
    }

    private linkKeyToStringKey(linkKey: ApiLinkKey, resourceType: string): string {
        const key = Object.keys(linkKey).filter(k => !k.startsWith("?"));
        key.sort(); // sort keys consistently
        return `${resourceType}/${key.join("/")}`;
    }

    private extractLastModified(data: any): string {
        if (data != null) {
            if (data.deletedOn != null) {
                try {
                    Date.parse(data.deletedOn);
                    return data.deletedOn;
                } catch {/* ignore errors */ }
            }
            if (data.updatedOn != null) {
                try {
                    Date.parse(data.updatedOn);
                    return data.updatedOn;
                } catch {/* ignore errors */ }
            }
            if (data.createdOn != null) {
                try {
                    Date.parse(data.createdOn);
                    return data.createdOn;
                } catch {/* ignore errors */ }
            }
        }
        return (new Date()).toUTCString();
    }

    private async cacheResults(request: RequestInfo, responseData: ApiResponse<unknown>) {
        if (this.apiCache == null) {
            return;
        }
        const isGet = typeof request === "string" || request.method === "GET";

        const embedded = responseData?.embedded;
        delete responseData.embedded; // nothing outside of caching must depend on this!

        const date = this.extractLastModified(responseData?.data);

        if (isGet) {
            // only cache the whole response for get requests
            this.apiCache.put(request, new Response(JSON.stringify(responseData), { headers: { "last-modified": date } }));
        } else {
            // if method could have deleted things
            const apiObject = responseData?.data as ApiObject;
            if (isChangedApiObject(apiObject)) {
                // invalidate changed object
                this.apiCache.delete(apiObject.changed.href);
                this.apiEmbeddedCache.delete(apiObject.changed.href);
                responseData.links.forEach(link => {
                    // invalidate all related changes
                    this.apiCache.delete(link.href);
                    this.apiEmbeddedCache.delete(link.href);
                });
            }
            if (isDeletedApiObject(apiObject)) {
                // Remove cache entries of deleted object
                // FIXME also delete related deleted resources in cache!!!
                this.apiCache.delete(apiObject.deleted.href);
                this.apiEmbeddedCache.delete(apiObject.deleted.href);
                responseData.links.forEach(link => {
                    // invalidate all related changes
                    this.apiCache.delete(link.href);
                    this.apiEmbeddedCache.delete(link.href);
                });
            }
        }

        if (embedded != null) {
            const promises = [];
            for (const response of embedded) {
                const selfLink = (response as ApiResponse<ApiObject>)?.data?.self?.href ?? null;
                if (selfLink == null) {
                    continue;
                }
                const date = this.extractLastModified(response?.data);
                const cache = this.apiEmbeddedCache ?? this.apiCache;
                promises.push(cache.put(selfLink, new Response(JSON.stringify(response), { headers: { "last-modified": date } })));
            }
            await Promise.all(promises);
        }
    }

    private async cacheKeyedLinks(responseData: ApiResponse<unknown>) {
        const keyedLinks = responseData.keyedLinks ?? [];
        keyedLinks.forEach(keyedLink => {
            const stringKey = this.keyedLinkToStringKey(keyedLink);
            if (this.keyedLinksByKey.has(stringKey)) {
                return;
            }
            this.keyedLinksByKey.set(stringKey, keyedLink);
            // cache by resource type
            if (!this.keyedLinkyByResourceType.has(keyedLink.resourceType)) {
                this.keyedLinkyByResourceType.set(keyedLink.resourceType, [keyedLink]);
                return;
            }
            const existingLinks = this.keyedLinkyByResourceType.get(keyedLink.resourceType);
            if (existingLinks.some(existing => keyedLink.key.every(key => existing.key.includes(key)))) {
                return; // Key already exists
            }
            existingLinks.push(keyedLink);
        });
    }

    private async handleResponse<T>(response: Response, input: RequestInfo): Promise<T> {
        if (!response.ok) {
            console.warn(response);
            throw new ResponseError("Something went wrong with the request!", response);
        }

        if (response.status === 204) {
            // no content
            return null;
        }

        const contentType = response.headers.get("content-type");

        if (contentType === "application/json") {
            const responseData = await response.json() as T;

            if (isApiResponse(responseData)) {
                this.cacheKeyedLinks(responseData);
                await this.cacheResults(input, responseData);
            }

            return responseData;
        } else if (contentType === "application/schema+json") {
            return await response.json() as T;
        } else {
            return response as unknown as T;
        }
    }

    private applyDefaultAuthorization(init: RequestInit): RequestInit {
        if (this._defaultAuthorization == null) {
            return init;
        }
        if (init?.headers != null) {
            if (Array.isArray(init.headers)) {
                if (init.headers.every(header => header[0] !== "Authorization")) {
                    init.headers.push(["Authorization", this._defaultAuthorization]);
                }
            } else {
                if (init.headers?.["Authorization"] == null) {
                    init.headers["Authorization"] = this._defaultAuthorization;
                }
            }
        }
        return init;
    }

    // eslint-disable-next-line complexity
    private async _fetchCached(input: Request, ignoreCache: boolean | "ignore-embedded" = false): Promise<Response | null> {
        if (this.apiCache == null || ignoreCache === true) {
            return null;
        }
        const directCached = await this.apiCache.match(input);
        if (this.apiEmbeddedCache != null) {
            const embeddedCached = await this.apiEmbeddedCache.match(input);
            if (directCached == null) {
                if (ignoreCache === "ignore-embedded") {
                    return null;
                }
                return embeddedCached;
            }
            if (embeddedCached != null) {
                const dateDirect = directCached.headers.get("last-modified");
                const dateEmbedded = embeddedCached.headers.get("last-modified");
                if (dateDirect && dateEmbedded) {
                    try {
                        const timeDirect = Date.parse(dateDirect);
                        const timeEmbedded = Date.parse(dateEmbedded);
                        if (timeDirect >= timeEmbedded) {
                            return directCached;
                        }
                        if (ignoreCache === "ignore-embedded") {
                            return null; // direct cached is stale but embedded cache result is to be ignored
                        }
                    } catch {/* ignore errors */ }
                }
            }
        }
        return directCached;
    }

    private async _fetch<T>(input: RequestInfo, ignoreCache: boolean | "ignore-embedded" = false, init: RequestInit = null): Promise<T> {
        if (init != null && Boolean(init)) {
            input = new Request(input, this.applyDefaultAuthorization(init));
        }
        if (typeof input === "string") {
            input = new Request(input, this.applyDefaultAuthorization({ headers: { Accept: "application/json" } }));
        }
        // FIXME caching
        const isGet = typeof input === "string" || input.method === "GET";
        if (isGet) {
            const response = await this._fetchCached(input, ignoreCache);
            if (response != null) {
                const responseData = await response.json();
                if (input.url === responseData.data.self.href) {
                    // prevent stale/incorrect cache results
                    return responseData as T;
                } else {
                    console.log("Wrong cached result!", input, responseData.data.self.href);
                }
            }
        }
        const rootResponse = await this.http.fetch(input);
        return await this.handleResponse<T>(rootResponse, input);
    }

    public async clearCaches(reopenCache: boolean = true) {
        if ("caches" in window) {
            // cache api available

            // remove refenrence to cache that should be deleted
            this.apiCache = null;
            this.apiEmbeddedCache = null;

            // delete all! caches
            const cacheNames = await caches.keys();
            for (const cacheName of cacheNames) {
                await caches.delete(cacheName);
            }

            if (reopenCache) {
                await this.openCache();
            }
        }

    }

    private async openCache() {
        if ("caches" in window) {
            // cache api available

            // delete unknown caches
            const expectedCacheNamesSet = new Set(Object.values(BaseApiService.CURRENT_CACHES));

            const cacheNames = await caches.keys();
            cacheNames.forEach(cacheName => {
                if (!expectedCacheNamesSet.has(cacheName)) {
                    caches.delete(cacheName);
                }
            });

            // open known cache
            this.apiCache = await caches.open(BaseApiService.CURRENT_CACHES.api);
            this.apiEmbeddedCache = await caches.open(BaseApiService.CURRENT_CACHES.apiEmbedded);
        }
    }

    private async resolveApiRootPromise<T>(resolve: (value?: ApiResponse<T> | PromiseLike<ApiResponse<T>>) => void, reject: (reason: any) => void) {
        await this.openCache();
        const api_versions = await this._fetch<ApiResponse<unknown>>(BaseApiService.API_ROOT_URL, true);
        const compatible_version: string = api_versions.data[BaseApiService.API_VERSION];
        if (compatible_version == null) {
            console.error("No compatible API version found!");
            reject(Error("No compatible API version found!"));
            return;
        }
        const version_root_link = this.resolveRel(api_versions.links, compatible_version);
        if (version_root_link == null) {
            console.error("No compatible API version found! The ref could not be resolved!");
            reject(Error("No compatible API version found! The ref could not be resolved!"));
            return;
        }
        const api_version_root = await this._fetch<ApiResponse<T>>(version_root_link.href, true);
        if (api_version_root == null) {
            console.error("No compatible API version found! The root of the api version could not be loaded!");
            reject(Error("No compatible API version found! The root of the api version could not be loaded!"));
            return;
        }
        this.prefetchRelsRecursive("api", api_version_root);
        resolve(api_version_root);
    }

    private async resolveRecursiveRels(rels: string | string[] | string[][], root?: ApiResponse<unknown>): Promise<ApiLink> {
        if (typeof rels === "string") {
            rels = [rels];
        }
        if (rels.length === 0) {
            throw new Error("Cannot resolve empty rel list!");
        }
        let base = root ?? await this.resolveApiRoot();
        for (let i = 0; i < rels.length; i++) {
            const rel = rels[i];
            const nextLink = this.resolveRel(base.links, rel);
            if (nextLink == null) {
                throw new Error(`Could not resolve rel "${rel}" for base ${JSON.stringify(base.links)}`);
            }
            if (i + 1 === rels.length) {
                return nextLink;
            }
            // not the last rel
            base = await this._fetch<ApiResponse<unknown>>(nextLink.href);
        }
    }

    private async _searchResolveRels(rel: string | string[], root?: ApiResponse<unknown>, apiRel: string | string[] = "api"): Promise<ApiLink> {
        const base = root ?? await this.resolveApiRoot();
        const matchingLinks = base.links.filter(link => matchesLinkRel(link, rel));
        if (matchingLinks.length > 0) {
            if (matchingLinks.length === 1) { // only one match
                return matchingLinks[0];
            }
            // prioritise match with resourceType
            const bestMatch = matchingLinks.find(link => (typeof rel === "string") ? link.resourceType === rel : rel.some(rel => link.resourceType === rel));
            return bestMatch ?? matchingLinks[0];
        }
        for (const link of base.links) {
            if (matchesLinkRel(link, apiRel)) {
                const newBase = await this._fetch<ApiResponse<unknown>>(link.href);
                const matchedLink = this._searchResolveRels(rel, newBase, apiRel);
                if (matchedLink != null) {
                    return matchedLink;
                }
            }
        }
        // no link found
        return null;
    }

    public async searchResolveRels(rel: string | string[]): Promise<ApiLink> {
        const link = await this._searchResolveRels(rel);
        if (link == null) {
            throw Error(`Could not find a link with the relation ${rel}!`);
        }
        return link;
    }

    private async resolveApiLinkKey(apiLinkKey: ApiLinkKey, resourceType: string, queryParams?: ApiLinkKey): Promise<ApiLink> {
        const key: ApiLinkKey = { ...apiLinkKey };
        if (queryParams != null) {
            Object.keys(queryParams).forEach(queryKeyVariable => {
                key[`?${queryKeyVariable}`] = queryParams[queryKeyVariable];
            });
        }
        const stringKey = this.linkKeyToStringKey(key, resourceType);
        if (!this.keyedLinksByKey.has(stringKey)) {
            throw Error(`No keyed link found for the api link key ${key}!`);
        }
        return applyKeyToLinkedKey(this.keyedLinksByKey.get(stringKey), key);
    }

    private fillOutKey(initialKey: ApiLinkKey, existingKeyVariables: string[], keyVariables: string[], keyValues: string[]): ApiLinkKey {
        const newKey: ApiLinkKey = { ...initialKey };
        let i = 0; // index for keyValuesList
        for (let k = 0; k < keyVariables.length; k++) {
            const keyVar = keyVariables[k];
            if (!existingKeyVariables.includes(keyVar)) {
                if (i >= keyValues.length) {
                    throw Error(`Cannot match keyed link ${keyVariables} with existing key ${existingKeyVariables}.`);
                }
                newKey[keyVar] = keyValues[i];
                i++; // increment index for keyValues list to use next value
            }
        }
        return newKey;
    }

    // eslint-disable-next-line complexity
    private async reconstructApiLinkKey(steps: Array<{ type: "rel" | "key", value: string }>, initialKey: ApiLinkKey): Promise<ApiLinkKey> {
        if (steps.length === 0) {
            throw Error("Empty client url.");
        }
        if (steps[0].type !== "rel") {
            throw Error("Malformed client url. Must start with a 'rel'!");
        }
        const resourceType = steps[0].value;
        const keyValues: string[] = [];
        for (let i = 1; i < steps.length; i++) {
            if (steps[i].type !== "key") {
                break;
            }
            keyValues.push(steps[i].value);
        }
        if (keyValues.length === 0) {
            const relevantLinks = this.keyedLinkyByResourceType.get(resourceType) ?? [];
            const link = relevantLinks.find(link => checkKeyMatchesKeyedLinkExact(initialKey, link));
            if (link != null) {
                return initialKey;
            }
            throw Error("Malformed client url. A rel must be followed by at least one key value!");
        }
        const nextSteps = steps.slice(1 + keyValues.length);
        const relevantKeys = this.keyedLinkyByResourceType.get(resourceType) ?? [];
        for (let i = 0; i < relevantKeys.length; i++) {
            const keyedLink = relevantKeys[i];
            const existingKeyVariables = Object.keys(initialKey);
            if (keyedLink.key.length !== (keyValues.length + existingKeyVariables.length)) {
                continue; // keys do not match in length
            }
            const keyVariables = [...keyedLink.key].sort();
            try {
                const newKey = this.fillOutKey(initialKey, existingKeyVariables, keyVariables, keyValues);
                if (nextSteps.length > 0) {
                    return this.reconstructApiLinkKey(nextSteps, newKey);
                } else {
                    return newKey;
                }
            } catch (error) {
                // could not reconstruct key with this keyed link as path
                // try next link
            }
        }
        throw Error("Could not reconstruct a valid key from the client url.");
    }

    public async buildClientUrl(selfLink: ApiLink, resourceKey: ApiLinkKey = {}): Promise<string> {
        const fullKey = selfLink.resourceKey ?? resourceKey;
        const resKey = { ...fullKey };
        const queryKey: string[] = [];
        if (resKey == null || Object.keys(resKey).length === 0) {
            return selfLink.resourceType;
        }
        const queryKeyVariables = Object.keys(resKey).filter(keyVariable => keyVariable.startsWith("?"));
        if (queryKeyVariables.length > 0) {
            queryKeyVariables.forEach(queryKeyVariable => {
                queryKey.push(`${queryKeyVariable.substring(1)}=${resKey[queryKeyVariable]}`);
                delete resKey[queryKeyVariable];
            });
            if (Object.keys(resKey).length === 0) {
                if (queryKey.length > 0) {
                    return `${selfLink.resourceType}?${queryKey.join("&")}`;
                } else {
                    return selfLink.resourceType;
                }
            }
        }
        const matchingKeys: Array<{ key: string[], queryKey: string[], rel: string, link: KeyedApiLink }> = [];

        this.keyedLinkyByResourceType.forEach((keyedLinks, resourceType) => {
            keyedLinks.forEach(keyedLink => {
                if (checkKeyMatchesKeyedLink(fullKey, keyedLink)) {
                    if (matchingKeys.some(match => {
                        if (match.key.length !== keyedLink.key.length || match.queryKey.length !== (keyedLink.queryKey?.length ?? 0)) {
                            return false; // key or query key do not match in length
                        }
                        if (match.rel !== keyedLink.resourceType) {
                            return false; // also discriminate keyed links by resource type!
                        }
                        return match.key.every(keyVar => keyedLink.key.includes(keyVar));
                    })) {
                        // key already in matching keys
                        return;
                    }
                    matchingKeys.push({
                        key: [...keyedLink.key].sort(),
                        queryKey: [...(keyedLink.queryKey ?? [])].sort(),
                        rel: resourceType,
                        link: keyedLink,
                    });
                }
            });
        });

        matchingKeys.sort((a, b) => {
            if (a.key.length !== b.key.length) {
                // sort by key length (primary)
                return a.key.length - b.key.length;
            }
            // then sort by queryKeyLength
            return a.queryKey.length - b.queryKey.length;
        });

        if (matchingKeys.length === 0) {
            throw Error("Could not find any matching key!");
        }
        const containsFullMatch = matchingKeys.some(match => checkKeyMatchesKeyedLinkExact(fullKey, match.link, selfLink.resourceType));
        if (!containsFullMatch) {
            console.info(selfLink, matchingKeys);
            throw Error("Could not find a fully matching key to build the client url with!");
        }

        const usedKeyVariables = new Set<string>();

        const url: string[] = [];

        let urlResourceType: string = null;

        matchingKeys.forEach(match => {
            if (match.key.every(keyVar => usedKeyVariables.has(keyVar))) {
                if (selfLink.resourceType !== urlResourceType && selfLink.resourceType === match.rel) {
                    // introduces bug if this link is not the last keyed link to consider
                    url.push(match.rel);
                    urlResourceType = match.rel; // workaround fix (together with below)
                }
                return;
            }
            if (urlResourceType !== match.rel) { // FIXME workaround for bug introduced above
                url.push(match.rel);
            }
            urlResourceType = match.rel;
            match.key.forEach(keyVar => {
                if (usedKeyVariables.has(keyVar)) {
                    return; // only append new keys
                }
                usedKeyVariables.add(keyVar);
                url.push(`:${resKey[keyVar]}`);
            });
            // put part in cache for later use
            const currentUrl = url.join("/");
            if (!this.clientUrlToApiLink.has(currentUrl)) {
                // TODO later fill in template in URL before caching...
                //this.clientUrlToApiLink.set(currentUrl, match.link);
            }
        });

        const concreteUrl = url.join("/");

        if (queryKey) {
            const query = queryKey.join("&");
            return `${concreteUrl}?${query}`;
        }

        return concreteUrl;
    }

    public async resolveLinkKey(apiKey: ApiLinkKey, resourceType?: string): Promise<ApiLink[]> {
        const foundLinks: ApiLink[] = [];

        if (resourceType != null) {
            this.keyedLinkyByResourceType.get(resourceType)?.forEach(keyedLink => {
                if (checkKeyCompatibleWithKeyedLink(apiKey, keyedLink, resourceType)) {
                    foundLinks.push(applyKeyToLinkedKey(keyedLink, apiKey));
                }
            });
        } else {
            this.keyedLinksByKey.forEach(keyedLink => {
                if (checkKeyCompatibleWithKeyedLink(apiKey, keyedLink)) {
                    foundLinks.push(applyKeyToLinkedKey(keyedLink, apiKey));
                }
            });
        }

        return foundLinks;
    }

    public async resolveClientUrl(clientUrl: string): Promise<ApiLink> { // FIXME remove query params
        await this.resolveApiRoot(); // must be connected to api for this!
        if (this.clientUrlToApiLink.has(clientUrl)) {
            return this.clientUrlToApiLink.get(clientUrl);
        }
        const queryParams: ApiLinkKey = {};
        let includesKey = false;
        let resourceType: string = null;
        const [path, search] = clientUrl.split("?");
        const steps: Array<{ type: "rel" | "key", value: string }> = path.split("/")
            .filter(step => step != null && step.length > 0)
            .map(step => {
                if (step.startsWith(":")) {
                    includesKey = true;
                    return { type: "key", value: step.substring(1) };
                }
                // set last known rel as resourceType
                resourceType = step;
                return { type: "rel", value: step };
            });
        if (search) {
            search.split("&").forEach(entry => {
                const [key, value] = entry.split("=");
                queryParams[key] = value;
            });
        }

        if (!includesKey) {
            const rels = steps.map(step => step.value);
            const resolvedLink = await this.searchResolveRels(rels);

            if (queryParams != null && Object.keys(queryParams).length > 0) {
                const query = Object.keys(queryParams)
                    .map(k => `${k}=${queryParams[k]}`)
                    .join("&");
                const queryStart = resolvedLink.href.includes("?") ? "&" : "?";
                return {
                    ...resolvedLink,
                    href: `${resolvedLink.href}${queryStart}${query}`,
                    resourceKey: { ...queryParams }, // FIXME add correct prefix for query params
                };
            }

            return resolvedLink;
        }
        const linkKey = await this.reconstructApiLinkKey(steps, {});

        return await this.resolveApiLinkKey(linkKey, resourceType, queryParams);
    }

    private async prefetchRelsRecursive(rel: string | string[] = "api", root?: ApiResponse<unknown>, ignoreCache: boolean | "ignore-embedded" = true) {
        const base = root ?? await this.resolveApiRoot();
        base.links.forEach(async (link) => {
            if (matchesLinkRel(link, rel)) {
                const new_base = await this._fetch<ApiResponse<unknown>>(link.href, ignoreCache);
                this.prefetchRelsRecursive(rel, new_base, ignoreCache);
            }
            if (matchesLinkRel(link, "nav")) {
                this.rootNavigationLinks.push(link);
            }
        });
    }

    private async resolveApiRoot(): Promise<ApiResponse<GenericApiObject>> {
        if (this.apiRoot != null) {
            return await this.apiRoot;
        }
        this.apiRoot = new Promise<ApiResponse<GenericApiObject>>((resolve, reject) => {
            this.resolveApiRootPromise<GenericApiObject>(resolve, reject);
        });
        return await this.apiRoot;
    }

    public async getRootNavigationLinks(): Promise<ApiLink[]> {
        await this.resolveApiRoot(); // await root links beeing resolved
        return this.rootNavigationLinks;
    }

    public async getByRel<T>(rel: string | string[] | string[][], ignoreCache: boolean | "ignore-embedded" = false): Promise<ApiResponse<T>> {
        const link: ApiLink = await this.resolveRecursiveRels(rel);
        return await this._fetch<ApiResponse<T>>(link.href, ignoreCache);
    }

    public async getByApiLink<T>(link: ApiLink, ignoreCache: boolean | "ignore-embedded" = false): Promise<ApiResponse<T>> {
        return await this._fetch<ApiResponse<T>>(link.href, ignoreCache);
    }

    public async submitByApiLink<T>(link: ApiLink, data?: any, signal?: AbortSignal, authentication?: string): Promise<ApiResponse<T>> {
        const method = link.rel.find(rel => rel === "post" || rel === "put" || rel === "patch" || rel === "delete")?.toUpperCase();
        const init: RequestInit = {
            headers: { Accept: "application/json", "Content-Type": "application/json" },
            method: method,
        };
        if (authentication != null) {
            // FIXME use more generic methods for injecting auth
            init.headers["Authorization"] = authentication;
        }
        if (data !== undefined) {
            init.body = JSON.stringify(data);
        }
        if (signal != null) {
            init.signal = signal;
        }
        if (link.rel.some(rel => rel === "requires-fresh-login")) {
            // wait for a fresh login to happen
            const authToken = await new Promise<string>((resolve, reject) => {
                this.events.publish(REQUEST_FRESH_LOGIN_CHANNEL, { resolve, reject });
            });
            init.headers["Authorization"] = `Bearer ${authToken}`;
        }
        const result = await this._fetch<ApiResponse<T>>(link.href, true, init);

        // check for logout handling
        if (isApiObject(result.data)) {
            if (matchesLinkRel(result.data.self, "logout")) {
                // result contains logout command
                this.events.publish(REQUEST_LOGOUT_CHANNEL);
            }
        }
        return result;
    }

    public async fetch<T>(input: RequestInfo, init?: RequestInit, ignoreCache: boolean | "ignore-embedded" = false): Promise<T> {
        return await this._fetch<T>(input, ignoreCache, init);
    }
}
