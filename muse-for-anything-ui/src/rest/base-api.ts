import { autoinject } from "aurelia-framework";
import { HttpClient } from "aurelia-fetch-client";
import { ApiResponse, ApiLink, GenericApiObject, ApiObject, matchesLinkRel } from "./api-objects";

@autoinject
export class BaseApiService {
    static API_VERSION = "v0.1";
    static API_ROOT_URL = "./api/";
    static CACHE_VERSION = 1;
    static CURRENT_CACHES = {
        api: `api-cache-v${BaseApiService.CACHE_VERSION}`,
    };

    private http;
    private apiRoot: Promise<ApiResponse<GenericApiObject>>;
    private apiCache: Cache;

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

    private async cacheResults(url, responseData: ApiResponse<unknown>) {
        if (this.apiCache == null) {
            return;
        }
        if (responseData?.embedded == null) {
            this.apiCache.put(url, new Response(JSON.stringify(responseData)));
        } else {
            const embedded = responseData.embedded;
            delete responseData.embedded;
            this.apiCache.put(url, new Response(JSON.stringify(responseData)));
            for (const response of embedded) {
                const selfLink = (response as ApiResponse<ApiObject>)?.data?.self?.href ?? null;
                if (selfLink == null) {
                    continue;
                }
                this.apiCache.put(selfLink, new Response(JSON.stringify(responseData)));
            }
        }
    }

    private async _get<T>(url: string, ignoreCache = false): Promise<ApiResponse<T>> {
        if (!ignoreCache && this.apiCache != null) {
            const response = await this.apiCache.match(url);
            if (response != null) {
                const responseData = await response.json();
                return responseData as ApiResponse<T>;
            }
        }
        const rootResponse = await this.http.fetch(url);
        const responseData = await rootResponse.json() as ApiResponse<T>;

        await this.cacheResults(url, responseData);

        return responseData;
    }

    private async clearCaches(reopenCache: boolean = true) {
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
        const api_versions = await this._get(BaseApiService.API_ROOT_URL, true);
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
        const api_version_root = await this._get<T>(version_root_link.href, true);
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
            base = await this._get(nextLink.href);
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
                const newBase = await this._get(link.href);
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

    private async prefetchRelsRecursive(rel: string | string[] = "api", root?: ApiResponse<unknown>, ignoreCache: boolean = true) {
        const base = root ?? await this.resolveApiRoot();
        base.links.forEach(async (link) => {
            if (matchesLinkRel(link, rel)) {
                const new_base = await this._get(link.href, ignoreCache);
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

    public async getByRel<T>(rel: string | string[] | string[][]): Promise<ApiResponse<T>> {
        const link: ApiLink = await this.resolveRecursiveRels(rel);
        return await this._get<T>(link.href);
    }

    public async get<T>(link: ApiLink): Promise<ApiResponse<T>> {
        return await this._get<T>(link.href);
    }
}
