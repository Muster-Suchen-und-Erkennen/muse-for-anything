import { bindable, autoinject } from "aurelia-framework";
import { ApiLink } from "rest/api-objects";
import { BaseApiService } from "rest/base-api";
import { NormalizedApiSchema, PropertyDescription } from "rest/schema-objects";


@autoinject
export class ResourceReferenceDefinitionView {
    @bindable data: any;
    @bindable schema: NormalizedApiSchema;
    @bindable context: any;

    referenceTypeProp: PropertyDescription;
    referenceType: string;
    resourceLink: ApiLink;

    private apiService: BaseApiService;

    constructor(apiService: BaseApiService) {
        this.apiService = apiService;
    }

    dataChanged(newValue, oldValue) {
        if (newValue == null) {
            this.referenceType = null;
            this.resourceLink = null;
            return;
        }
        this.referenceType = `resource-type.${newValue.referenceType}`;
        if (newValue.referenceKey != null) {
            this.apiService.resolveLinkKey(newValue.referenceKey, newValue.referenceType).then(links => {
                this.resourceLink = links.find(link => !link.rel.some(rel => rel === "collection"));
            });
        } else {
            this.resourceLink = null;
        }
    }

    schemaChanged(newValue: NormalizedApiSchema, oldValue) {
        if (newValue == null) {
            this.referenceTypeProp = null;
            return;
        }
        if (newValue.normalized.customType !== "resourceReferenceDefinition") {
            console.warn("Resource reference definition view used with wrong schema!", newValue);
        }
        this.referenceTypeProp = newValue.getPropertyList(["referenceType"], { "allowList": ["referenceType"] })?.[0];
    }
}
