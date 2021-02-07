import { bindable, autoinject, observable } from "aurelia-framework";
import { EventAggregator, Subscription } from "aurelia-event-aggregator";
import { BaseApiService } from "rest/base-api";
import { ApiLink, ApiLinkKey, ApiObject, ApiResponse } from "rest/api-objects";
import { NavigationLinksService } from "services/navigation-links";
import { API_RESOURCE_CHANGES_CHANNEL } from "resources/events";


interface TaxonomyApiObject extends ApiObject {
    name: string;
    description: string | null;
    items: ApiLink[];
}

interface TaxonomyItemApiObject extends ApiObject {
    name: string;
    description: string | null;
    parents: ApiLink[];
    children: ApiLink[];
    // TODO missing
}

interface TaxonomyItemRelationApiObject extends ApiObject {
    sourceItem: ApiLink;
    targetItem: ApiLink;
}


@autoinject
export class TaxonomyGraph {
    @bindable apiLink;
    @bindable ignoreCache = false;

    @observable apiObject: TaxonomyApiObject;

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
        this.apiObject = null;
        this.loadData(this.apiLink, this.ignoreCache);
    }

    private loadData(apiLink: ApiLink, ignoreCache: boolean) {
        this.api.getByApiLink<TaxonomyApiObject>(apiLink, ignoreCache).then(apiResponse => {
            if (apiResponse.data.self.resourceType !== "ont-taxonomy") {
                console.error("Can only display graph for taxonomy objects!", apiResponse.data);
                return;
            }
            this.apiObject = apiResponse.data; // FIXME use proper type checking for api response…
        });
    }

    apiObjectChanged(newValue: TaxonomyApiObject, oldValue) {
        if (newValue == null) {
            // TODO reset graph!
            return;
        }
        const itemPromises = [];
        const relationPromises = [];
        const items: TaxonomyItemApiObject[] = [];
        const relations: TaxonomyItemRelationApiObject[] = [];
        newValue.items.forEach(itemLink => {
            itemPromises.push(this.api.getByApiLink<TaxonomyItemApiObject>(itemLink, false).then(apiResponse => {
                items.push(apiResponse.data);
                apiResponse.data.children.forEach(childRelationLink => {
                    relationPromises.push(this.api.getByApiLink<TaxonomyItemRelationApiObject>(childRelationLink, false).then(relationApiResponse => {
                        relations.push(relationApiResponse.data);
                    }));
                });
            }));
        });
        Promise.all(itemPromises).then(() => Promise.all(relationPromises)).then(() => this.setTaxonomyData(items, relations));
    }

    private setTaxonomyData(items: TaxonomyItemApiObject[], relations: TaxonomyItemRelationApiObject[]) {
        console.log(items, relations)
    }

    detached() {
        this.subscription?.dispose();
    }
}
