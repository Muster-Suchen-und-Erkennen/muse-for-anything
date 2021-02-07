import { autoinject } from "aurelia-framework";
import { EventAggregator, Subscription } from "aurelia-event-aggregator";
import { activationStrategy } from "aurelia-router";
import { NavigationLinksService, NavLinks } from "services/navigation-links";
import { BaseApiService } from "rest/base-api";
import { ApiLink, ApiLinkKey, ApiResponse, isApiObject } from "rest/api-objects";
import { API_RESOURCE_CHANGES_CHANNEL, NAV_LINKS_CHANNEL } from "resources/events";

const NESTED_SCHEMA_OBJECT_TYPES = new Set(["ont-type", "ont-type-version"]);
const NESTED_DATA_OBJECT_TYPES = new Set(["ont-object", "ont-object-version"]);

@autoinject
export class UpdateContent {

    updateResourceType: string;
    updateApiLink: ApiLink;

    initialData: any;

    private api: BaseApiService;
    private events: EventAggregator;
    private navService: NavigationLinksService;
    private navSubscription: Subscription;
    private changeSubscription: Subscription;

    private path: string;
    private currentResponse: ApiResponse<unknown>;

    constructor(baseApi: BaseApiService, events: EventAggregator, navService: NavigationLinksService) {
        this.api = baseApi;
        this.events = events;
        this.navService = navService;
        this.subscribe();
    }

    subscribe(): void {
        this.navSubscription = this.events.subscribe(NAV_LINKS_CHANNEL, (navLinks: NavLinks) => {
            if (true && navLinks.actions?.length > 0) {
                const actionLink = navLinks.actions.find(actionLink => {
                    if (actionLink.actionType !== "update") {
                        return false;
                    }
                    return actionLink.apiLink?.resourceType === this.updateResourceType;
                });
                this.updateApiLink = actionLink?.apiLink;
            } else {
                this.updateApiLink = null;
            }
        });
        this.changeSubscription = this.events.subscribe(API_RESOURCE_CHANGES_CHANNEL, (resourceKey: ApiLinkKey) => {
            console.log("Possible change", resourceKey)
            if (!isApiObject(this.currentResponse?.data)) {
                return;
            }
            const selfKey: ApiLinkKey = this.currentResponse?.data?.self.resourceKey;
            if (selfKey == null || Object.keys(selfKey).length === 0) {
                return;
            }
            if (Object.keys(selfKey).every(key => selfKey[key] === resourceKey[key])) {
                // current object is a sub key
                console.log("Data changed, reloading...")
                this.loadData(this.currentResponse.data.self, false);
            }
        });
    }

    detached() {
        this.navSubscription?.dispose();
        this.changeSubscription?.dispose();
    }

    determineActivationStrategy() {
        return activationStrategy.invokeLifecycle;
    }

    activate(routeParams: { path: string, resourceType: string, [prop: string]: string }) {
        this.updateApiLink = null;
        this.initialData = undefined;
        this.path = routeParams.path;
        this.updateResourceType = routeParams.resourceType;
        const queryParams = { ...routeParams };
        delete queryParams.path;
        delete queryParams.resourceType;
        this.api.resolveClientUrl(this.path, queryParams)
            .then(link => {
                return this.loadData(link, true);
            });
    }

    private loadData(link: ApiLink, ignoreCache: boolean) {
        this.api.getByApiLink(link, ignoreCache)
            .then(response => {
                this.currentResponse = response;
                if (isApiObject(response.data) && response.data.self.resourceType === this.updateResourceType) {
                    let initialData;
                    if (NESTED_SCHEMA_OBJECT_TYPES.has(this.updateResourceType)) {
                        initialData = {
                            ...((response.data as any)?.schema ?? {}),
                        };
                    } else if (NESTED_DATA_OBJECT_TYPES.has(this.updateResourceType)) {
                        initialData = {
                            ...((response.data as any)?.data ?? {}),
                        };
                    } else {
                        initialData = {
                            ...response.data,
                        };
                    }
                    delete initialData.self;
                    console.log(initialData)
                    window.setTimeout(() => {
                        this.initialData = initialData;
                    }, 50); // FIXME remove bad waiting workaround for race conditions…
                }
                this.navService.setMainApiResponse(this.currentResponse);
            });
    }
}
