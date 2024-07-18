import { EventAggregator } from "aurelia-event-aggregator";
import { autoinject, bindable } from "aurelia-framework";
import { ApiLink, ApiObject } from "rest/api-objects";
import { BaseApiService } from "rest/base-api";
import { RESOURCE_TYPE_ICONS } from "services/navigation-links";

interface NavOption {
    link: ApiLink;
    clientUrl: string;
    title: string;
    icon: string;
}

@autoinject
export class CardNavIcons {
    @bindable apiObject: ApiObject;
    @bindable main: string;
    @bindable extra: string[] = [];
    @bindable skipNavigation: boolean = false;

    navOptions: Map<string, NavOption> = new Map();

    loading: boolean = true;

    private api: BaseApiService;

    constructor(baseApi: BaseApiService, events: EventAggregator) {
        this.api = baseApi;
    }

    apiObjectChanged(newValue: ApiObject) {
        this.loading = true;
        if (newValue == null) {
            return;
        }
        // fetch nav links
        this.api.getByApiLink(newValue.self).then(resource => {
            const navOptions: Map<string, NavOption> = new Map();
            const promises: Promise<unknown>[] = [];
            resource.links.forEach(link => {
                if (!link.rel.some(rel => rel === "nav" || rel === "up")) {
                    return;
                }
                if (link.rel.some(rel => rel === "collection")) {
                    return; // do not show collection resources as nav icons
                }

                promises.push(this.api.buildClientUrl(link).then(clientUrl => {
                    navOptions.set(link.resourceType, {
                        link: link,
                        clientUrl: `/explore/${clientUrl}`,
                        title: link.name ?? "",
                        icon: RESOURCE_TYPE_ICONS.get(link.resourceType) ?? "",
                    });
                }));
            });
            Promise.all(promises).then(() => {
                this.navOptions = navOptions;
                this.loading = false;
            });
        });
    }
}
