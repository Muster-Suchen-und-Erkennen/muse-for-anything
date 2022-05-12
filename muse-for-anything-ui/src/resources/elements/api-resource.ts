import { EventAggregator, Subscription } from "aurelia-event-aggregator";
import { autoinject, bindable } from "aurelia-framework";
import { PLATFORM } from "aurelia-pal";
import { API_RESOURCE_CHANGES_CHANNEL, AUTH_EVENTS_CHANNEL } from "resources/events";
import { ApiLink, ApiLinkKey, ApiObject, ApiResponse } from "rest/api-objects";
import { LOGIN, LOGIN_TOKEN_REFRESHED, LOGOUT } from "rest/authentication-service";
import { BaseApiService } from "rest/base-api";
import { NavigationLinksService } from "services/navigation-links";

// A resource map mapping from resource type relation to aurelia component
// Also update the imports in the HTML part!
const RESOURCE_MAP = {
    "collection": PLATFORM.moduleName("../api-object/collection"),
    "ont-namespace": PLATFORM.moduleName("../api-object/ont-namespace"),
    "ont-object-version": PLATFORM.moduleName("../api-object/ont-object-version"),
    "ont-object": PLATFORM.moduleName("../api-object/ont-object"),
    "ont-taxonomy-item-relation": PLATFORM.moduleName("../api-object/ont-taxonomy-item-relation"),
    "ont-taxonomy-item-version": PLATFORM.moduleName("../api-object/ont-taxonomy-item-version"),
    "ont-taxonomy-item": PLATFORM.moduleName("../api-object/ont-taxonomy-item"),
    "ont-taxonomy": PLATFORM.moduleName("../api-object/ont-taxonomy"),
    "ont-type-version": PLATFORM.moduleName("../api-object/ont-type-version"),
    "ont-type": PLATFORM.moduleName("../api-object/ont-type"),
    "page": PLATFORM.moduleName("../api-object/page"),
    "user-grant": PLATFORM.moduleName("../api-object/user-grant"),
    "user-role": PLATFORM.moduleName("../api-object/user-role"),
    "user": PLATFORM.moduleName("../api-object/user"),
};

@autoinject
export class ApiResource {
    @bindable isObjectChooser = false;
    @bindable skipNavigation = false;
    @bindable isMain = false;
    @bindable isRoot;
    @bindable apiLink;

    apiObject: ApiObject;
    modelData: { apiObject: ApiObject, apiResponse: ApiResponse<unknown>, isRoot: boolean, skipNavigation: boolean, isObjectChooser: boolean, onObjectSelect?: (object: any) => void };
    objectType: string;

    private lastStatus: number;

    private api: BaseApiService;
    private navService: NavigationLinksService;
    private events: EventAggregator;

    private changeSubscription: Subscription;
    private authChangesSubscription: Subscription;

    constructor(baseApi: BaseApiService, navService: NavigationLinksService, events: EventAggregator) {
        this.api = baseApi;
        this.navService = navService;
        this.events = events;
        this.subscribe();
    }

    subscribe(): void {
        this.changeSubscription = this.events.subscribe(API_RESOURCE_CHANGES_CHANNEL, (resourceKey: ApiLinkKey) => {
            const selfKey: ApiLinkKey = this.apiObject?.self.resourceKey;
            if (selfKey == null || Object.keys(selfKey).length === 0) {
                return;
            }
            if (Object.keys(selfKey).every(key => selfKey[key] === resourceKey[key])) {
                // current object is a sub key
                this.loadData(this.apiLink, false);
            }
        });
        this.authChangesSubscription = this.events.subscribe(AUTH_EVENTS_CHANNEL, (authEvent: string) => {
            if (authEvent === LOGOUT) {
                this.objectType = null;
                this.apiObject = null;
                this.modelData = null;
                // can load from cache as cache is deleted on logout
                this.loadData(this.apiLink, false);
            }
            if (authEvent === LOGIN) {
                // always reload regardless of last status because links can change
                // ignore cache if last result was successfully loaded to load resource from server!
                const ignoreCache = this.lastStatus >= 200 && this.lastStatus < 300;
                this.loadData(this.apiLink, ignoreCache);
            }
            if (authEvent === LOGIN_TOKEN_REFRESHED) {
                if (this.lastStatus === 401) {
                    // try again on token refresh, but only after auth failure
                    this.loadData(this.apiLink, false);
                }
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
            this.lastStatus = 200;
            this.apiObject = apiResponse.data;
            this.modelData = {
                apiObject: apiResponse.data,
                apiResponse: apiResponse,
                isRoot: Boolean(this.isRoot),
                skipNavigation: Boolean(this.skipNavigation),
                isObjectChooser: Boolean(this.isObjectChooser),
                onObjectSelect: (object) => console.log(object),
            };
            if (isMain) {
                this.navService.setMainApiResponse(apiResponse);
            }
            const rels = apiResponse.data.self.rel;
            if (rels.some(rel => rel === "page")) {
                this.objectType = RESOURCE_MAP["page"];
                return;
            }
            if (rels.some(rel => rel === "collection")) {
                this.objectType = RESOURCE_MAP["collection"];
                return;
            }
            const resourceView = RESOURCE_MAP[apiResponse.data.self.resourceType];
            // FIXME display some default component for unknown resources
            this.objectType = resourceView;
        }, err => {
            this.lastStatus = err.status ?? 500;
        });
    }

    detached() {
        this.changeSubscription?.dispose();
        this.authChangesSubscription?.dispose();
        if (this.isMain) {
            this.navService.setMainApiResponse(null);
        }
    }
}
