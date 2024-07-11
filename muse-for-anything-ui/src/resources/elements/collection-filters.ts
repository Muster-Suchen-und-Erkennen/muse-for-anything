import { EventAggregator } from "aurelia-event-aggregator";
import { autoinject, bindable } from "aurelia-framework";
import { Router } from "aurelia-router";
import { nanoid } from "nanoid";
import { DIALOG_ROUTING_CHANNEL } from "resources/events";
import { ApiLink, CollectionFilter } from "rest/api-objects";
import { BaseApiService } from "rest/base-api";

@autoinject
export class CollectionFilters {
    @bindable collection: ApiLink;
    @bindable filters: CollectionFilter[] = [];
    @bindable skipNavigation: boolean = false;

    slug = nanoid(8);

    searchFilterKey: string | null = null;
    searchFilterValue: string = "";

    private domNode: Element;
    private api: BaseApiService;
    private router: Router;
    private events: EventAggregator;

    constructor(element: Element, baseApi: BaseApiService, events: EventAggregator, router: Router) {
        this.domNode = element;
        this.api = baseApi;
        this.router = router;
        this.events = events;
    }

    filtersChanged(newValue, oldValue) {
        if (newValue == null) {
            newValue = [];
        }
        const searchFilter = newValue.find(filter => filter.type === "search");
        this.searchFilterKey = searchFilter?.key ?? null;
        this.updateCurrentFilterValues();
    }

    collectionChanged(newValue, oldValue) {
        this.updateCurrentFilterValues();
    }

    private updateCurrentFilterValues() {
        const key = this.collection.resourceKey ?? {};

        if (this.searchFilterKey) {
            this.searchFilterValue = key[this.searchFilterKey];
        }
    }


    onSearch() {
        this.navigateToFilter();
    }



    private navigateToFilter() {
        if (this.collection == null) {
            return;
        }

        // create local copy that can be safely modified
        const targetLink = { ...this.collection };
        const targetUrl = new URL(targetLink.href);
        const targetKey = { ...(targetLink.resourceKey ?? {}) };
        targetLink.resourceKey = targetKey;

        if (this.searchFilterKey?.startsWith("?")) {
            if (this.searchFilterValue) {
                targetKey[this.searchFilterKey] = this.searchFilterValue;
                targetUrl.searchParams.set(this.searchFilterKey.substring(1), this.searchFilterValue);
            } else {
                delete targetKey[this.searchFilterKey];
                targetUrl.searchParams.delete(this.searchFilterKey.substring(1));
            }
        }

        targetLink.href = targetUrl.toString();

        if (this.skipNavigation) {
            this.events.publish(DIALOG_ROUTING_CHANNEL, {
                "source": this.domNode,
                "link": targetLink,
            });
            return;
        }

        this.api.buildClientUrl(targetLink)
            .then(clientUrl => {
                this.router.navigate(`/explore/${clientUrl}`);
            });
    }
}

