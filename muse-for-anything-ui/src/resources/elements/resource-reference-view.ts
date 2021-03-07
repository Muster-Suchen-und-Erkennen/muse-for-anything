import { bindable, autoinject } from "aurelia-framework";
import { ApiLink } from "rest/api-objects";
import { BaseApiService } from "rest/base-api";
import { NormalizedApiSchema } from "rest/schema-objects";


@autoinject
export class ResourceReferenceView {
    @bindable data: any;
    @bindable schema: NormalizedApiSchema;

    resourceLink: ApiLink;

    private apiService: BaseApiService;

    constructor(apiService: BaseApiService) {
        this.apiService = apiService;
    }

    dataChanged(newValue, oldValue) {
        if (newValue == null) {
            this.resourceLink = null;
            return;
        }
        this.apiService.resolveLinkKey(newValue.referenceKey, newValue.referenceType).then(links => {
            this.resourceLink = links.find(link => !link.rel.some(rel => rel === "collection"));
        });
    }

    schemaChanged(newValue, oldValue) {
        if (newValue == null) {
            return;
        }
        if (newValue.normalized.customType !== "resourceReference") {
            console.warn("Resource reference view used with wrong schema!", newValue);
        }
    }
}
