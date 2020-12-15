import { autoinject } from "aurelia-framework";
import { EventAggregator, Subscription } from "aurelia-event-aggregator";
import { activationStrategy, RoutableComponentDetermineActivationStrategy } from "aurelia-router";
import { NavigationLinksService, NavLinks } from "services/navigation-links";
import { BaseApiService } from "rest/base-api";
import { ApiLink, ApiResponse } from "rest/api-objects";
import { NAV_LINKS_CHANNEL } from "resources/events";

@autoinject
export class CreateContent {

    createResourceType: string;
    createApiLink: ApiLink;

    private api: BaseApiService;
    private events: EventAggregator;
    private navService: NavigationLinksService;
    private subscription: Subscription;

    private path: string;
    private currentResponse: ApiResponse<unknown>;

    constructor(baseApi: BaseApiService, events: EventAggregator, navService: NavigationLinksService) {
        this.api = baseApi;
        this.events = events;
        this.navService = navService;
        this.subscribe();
    }

    subscribe(): void {
        this.subscription = this.events.subscribe(NAV_LINKS_CHANNEL, (navLinks: NavLinks) => {
            if (true && navLinks.actions?.length > 0) {
                const actionLink = navLinks.actions.find(actionLink => {
                    if (actionLink.actionType !== "create") {
                        return false;
                    }
                    return actionLink.apiLink?.resourceType === this.createResourceType;
                });
                this.createApiLink = actionLink?.apiLink;
            } else {
                this.createApiLink = null;
            }
        });
    }

    detached() {
        this.subscription?.dispose();
    }

    determineActivationStrategy() {
        return activationStrategy.invokeLifecycle;
    }

    activate(routeParams: { path: string, resourceType: string, [prop: string]: string }) {
        this.createApiLink = null;
        this.path = routeParams.path;
        this.createResourceType = routeParams.resourceType;
        const queryParams = { ...routeParams };
        delete queryParams.path;
        delete queryParams.resourceType;
        this.api.resolveClientUrl(this.path, queryParams)
            .then(link => {
                return this.api.getByApiLink(link);
            })
            .then(response => {
                this.currentResponse = response;
                this.navService.setMainApiResponse(this.currentResponse);
            });
    }

}
