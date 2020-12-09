import { bindable, autoinject } from "aurelia-framework";
import { EventAggregator, Subscription } from "aurelia-event-aggregator";
import { BaseApiService } from "rest/base-api";
import { ApiLink, ApiLinkKey, ApiObject, ApiResponse } from "rest/api-objects";
import { NavigationLinksService } from "services/navigation-links";
import { API_RESOURCE_CHANGES_CHANNEL } from "resources/events";

@autoinject
export class ApiResource {
    @bindable isMain = false;
    @bindable isRoot;
    @bindable apiLink;

    apiObject: ApiObject;
    modelData: { apiObject: ApiObject, apiResponse: ApiResponse<unknown>, isRoot: boolean };
    objectType: string;

    private api: BaseApiService;
    private navService: NavigationLinksService;
    private events: EventAggregator;

    private subscription: Subscription;

    constructor(baseApi: BaseApiService, navService: NavigationLinksService, events: EventAggregator) {
        this.api = baseApi;
        this.navService = navService;
        this.events = events;
        this.subscribe();
    }

    subscribe(): void {
        this.subscription = this.events.subscribe(API_RESOURCE_CHANGES_CHANNEL, (resourceKey: ApiLinkKey) => {
            const selfKey: ApiLinkKey = this.apiObject?.self.resourceKey;
            if (selfKey == null || Object.keys(selfKey).length === 0) {
                return;
            }
            if (Object.keys(selfKey).every(key => selfKey[key] === resourceKey[key])) {
                // current object is a sub key
                this.loadData(this.apiLink, false);
            }
        });
    }

    apiLinkChanged(newValue: ApiLink, oldValue) {
        this.objectType = null;
        this.apiObject = null;
        this.modelData = null;
        const ignoreCache = Boolean(this.isRoot);
        this.loadData(this.apiLink, ignoreCache);
    }

    private loadData(apiLink: ApiLink, ignoreCache: boolean) {
        const isMain = Boolean(this.isMain);
        this.api.getByApiLink<ApiObject>(apiLink, ignoreCache).then(apiResponse => {
            this.apiObject = apiResponse.data;
            this.modelData = {
                apiObject: apiResponse.data,
                apiResponse: apiResponse,
                isRoot: Boolean(this.isRoot),
            };
            if (isMain) {
                this.navService.setMainApiResponse(apiResponse);
            }
            const rels = apiResponse.data.self.rel;
            if (rels.some(rel => rel === "page")) {
                this.objectType = "page";
                return;
            }
            if (rels.some(rel => rel === "collection")) {
                this.objectType = "collection";
                return;
            }
            this.objectType = apiResponse.data.self.resourceType;
        });
    }

    detached() {
        this.subscription?.dispose();
        if (this.isMain) {
            this.navService.setMainApiResponse(null);
        }
    }
}
