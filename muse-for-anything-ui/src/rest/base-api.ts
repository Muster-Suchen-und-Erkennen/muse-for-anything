import { autoinject } from "aurelia-framework";
import { HttpClient } from "aurelia-fetch-client";
import { ApiResponse, ApiLink, GenericApiObject, ApiObject, matchesLinkRel, ApiLinkKey, KeyedApiLink, applyKeyToLinkedKey, checkKeyMatchesKeyedLink, isApiResponse, checkKeyMatchesKeyedLinkExact } from "./api-objects";

@autoinject
export class BaseApiService {
    static API_VERSION = "v0.1";
    static API_ROOT_URL = "./api/";
    static CACHE_VERSION = 1;
    static CURRENT_CACHES = {
        api: `api-cache-v${BaseApiService.CACHE_VERSION}`,
    };

    private http: HttpClient;
    private apiRoot: Promise<ApiResponse<GenericApiObject>>;
    private apiCache: Cache;

    private clientUrlToApiLink: Map<string, ApiLink> = new Map();
    private keyedLinksByKey: Map<string, KeyedApiLink> = new Map();
    private keyedLinkyByResourceType: Map<string, KeyedApiLink[]> = new Map();

    constructor(http: HttpClient) {
        this.http = http;
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

    private async cacheResults(request: RequestInfo, responseData: ApiResponse<unknown>) {
        if (this.apiCache == null) {
            return;
        }
        const isGet = typeof request === "string" || request.method === "GET";

        const embedded = responseData?.embedded;
        delete responseData.embedded; // nothing outside of caching must depend on this!

        if (isGet) {
            // only cache the whole response for get requests
            this.apiCache.put(request, new Response(JSON.stringify(responseData)));
        }

        if (embedded != null) {
            const promises = [];
            for (const response of embedded) {
                const selfLink = (response as ApiResponse<ApiObject>)?.data?.self?.href ?? null;
                if (selfLink == null) {
                    continue;
                }
                promises.push(this.apiCache.put(selfLink, new Response(JSON.stringify(response))));
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
            throw Error("Something went wrong with the request!");
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

    private async _fetch<T>(input: RequestInfo, ignoreCache = false, init: RequestInit = null): Promise<T> {
        if (init != null && Boolean(init)) {
            input = new Request(input, init);
        }
        if (typeof input === "string") {
            input = new Request(input, { headers: { Accept: "application/json" } });
        }
        const isGet = typeof input === "string" || input.method === "GET";
        if (isGet && !ignoreCache && this.apiCache != null) {
            const response = await this.apiCache.match(input);
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
        const link = base.links.find(link => matchesLinkRel(link, rel));
        if (link != null) {
            return link;
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
                            return false;
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
        const containsFullMatch = matchingKeys.some(match => checkKeyMatchesKeyedLinkExact(fullKey, match.link));
        if (!containsFullMatch) {
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

    public async resolveClientUrl(clientUrl: string, queryParams?: ApiLinkKey): Promise<ApiLink> {
        await this.resolveApiRoot(); // must be connected to api for this!
        if (this.clientUrlToApiLink.has(clientUrl)) {
            return this.clientUrlToApiLink.get(clientUrl);
        }
        let includesKey = false;
        let resourceType: string = null;
        const steps: Array<{ type: "rel" | "key", value: string }> = clientUrl.split("/")
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
        if (!includesKey) {
            const rels = steps.map(step => step.value);
            const resolvedLink = await this.searchResolveRels(rels);

            if (Object.keys(queryParams).length > 0) {
                const query = Object.keys(queryParams)
                    .map(k => `${k}=${queryParams[k]}`)
                    .join("&");
                return {
                    ...resolvedLink,
                    href: `${resolvedLink.href}?${query}`,
                    resourceKey: { ...queryParams },
                };
            }

            return resolvedLink;
        }
        const linkKey = await this.reconstructApiLinkKey(steps, {});

        return await this.resolveApiLinkKey(linkKey, resourceType, queryParams);
    }

    private async prefetchRelsRecursive(rel: string | string[] = "api", root?: ApiResponse<unknown>, ignoreCache: boolean = true) {
        const base = root ?? await this.resolveApiRoot();
        base.links.forEach(async (link) => {
            if (matchesLinkRel(link, rel)) {
                const new_base = await this._fetch<ApiResponse<unknown>>(link.href, ignoreCache);
                this.prefetchRelsRecursive(rel, new_base, ignoreCache);
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

    public async getByRel<T>(rel: string | string[] | string[][], ignoreCache: boolean = false): Promise<ApiResponse<T>> {
        const link: ApiLink = await this.resolveRecursiveRels(rel);
        return await this._fetch<ApiResponse<T>>(link.href, ignoreCache);
    }

    public async getByApiLink<T>(link: ApiLink, ignoreCache: boolean = false): Promise<ApiResponse<T>> {
        return await this._fetch<ApiResponse<T>>(link.href, ignoreCache);
    }

    public async submitByApiLink<T>(link: ApiLink, data?: any, signal?: AbortSignal): Promise<ApiResponse<T>> {
        const method = link.rel.find(rel => rel === "post" || rel === "put" || rel === "patch" || rel === "delete").toUpperCase();
        const init: RequestInit = {
            headers: { Accept: "application/json", "Content-Type": "application/json" },
            method: method,
        };
        if (data !== undefined) {
            init.body = JSON.stringify(data);
        }
        if (signal != null) {
            init.signal = signal;
        }
        return await this._fetch<ApiResponse<T>>(link.href, true, init);
    }

    public async fetch<T>(input: RequestInfo, init?: RequestInit, ignoreCache: boolean = false): Promise<T> {
        return await this._fetch<T>(input, ignoreCache, init);
    }
}
