import { bindable, autoinject } from "aurelia-framework";
import { EventAggregator } from "aurelia-event-aggregator";
import { BaseApiService } from "rest/base-api";
import { NavigationLink } from "services/navigation-links";
import { API_RESOURCE_CHANGES_CHANNEL } from "resources/events";
import { isChangedApiObject } from "rest/api-objects";

@autoinject
export class ActionLink {
    @bindable action: NavigationLink;

    private api: BaseApiService;
    private events: EventAggregator;

    constructor(baseApi: BaseApiService, events: EventAggregator) {
        this.api = baseApi;
        this.events = events;
    }

    performAction() {
        this.api.submitByApiLink(this.action.apiLink).then(result => {
            if (isChangedApiObject(result.data)) {
                this.events.publish(API_RESOURCE_CHANGES_CHANNEL, result.data.changed.resourceKey);
            }
        });
    }
}
