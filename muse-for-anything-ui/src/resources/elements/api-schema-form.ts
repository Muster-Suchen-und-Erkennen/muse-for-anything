import { bindable, autoinject, observable, bindingMode } from "aurelia-framework";
import { Router } from "aurelia-router";
import { BindingSignaler } from "aurelia-templating-resources";
import { ApiLink, isApiObject, isNewApiObject } from "rest/api-objects";
import { BaseApiService } from "rest/base-api";
import { NormalizedApiSchema } from "rest/schema-objects";
import { SchemaService } from "rest/schema-service";

@autoinject
export class ApiSchemaForm {
    @bindable initialData;
    @bindable apiLink: ApiLink;
    @bindable({ defaultBindingMode: bindingMode.fromView }) data: any;
    @bindable({ defaultBindingMode: bindingMode.fromView }) valid: boolean;
    @bindable({ defaultBindingMode: bindingMode.fromView }) submitting: boolean = false;
    @bindable({ defaultBindingMode: bindingMode.fromView }) abortSignal: AbortSignal;
    @bindable({ defaultBindingMode: bindingMode.fromView }) submitSuccess: boolean = false;
    @bindable({ defaultBindingMode: bindingMode.fromView }) submitError: boolean = false;

    @observable schema: NormalizedApiSchema;
    resourceTypeTranslationKey: string;


    private api: BaseApiService;
    private schemaService: SchemaService;

    private bindingSignaler: BindingSignaler;
    private router: Router;

    constructor(schemaService: SchemaService, basApi: BaseApiService, bindingSingaler: BindingSignaler, router: Router) {
        this.schemaService = schemaService;
        this.api = basApi;

        this.bindingSignaler = bindingSingaler;
        this.router = router;
    }

    apiLinkChanged(newValue: ApiLink, oldValue) {
        this.schema = null;
        if (newValue == null) {
            this.resourceTypeTranslationKey = null;
            return;
        }

        this.resourceTypeTranslationKey = `resource-type.${newValue.resourceType}`;
        if (newValue?.schema == null) {
            console.error("Api link does not have a schema!", newValue);
        }
        const fragment = this.schemaService.getSchemaFragmentFromUrl(newValue.schema);
        this.schemaService.getSchema(newValue.schema)
            .then(schema => schema.getNormalizedApiSchema(fragment))
            .then(normalizedSchema => this.schema = normalizedSchema);
    }

    schemaChanged(newValue, oldValue) {
        setTimeout(() => this.bindingSignaler.signal("revalidate"), 50);
        setTimeout(() => this.bindingSignaler.signal("update-values"), 50);
    }

    reset() {
        console.error("Currently not implemented!");
    }

    submit() {
        if (this.submitting) {
            return;
        }
        if (!this.valid) {
            console.warn("Tried to submit a form that is not valid!");
            return;
        }
        console.log(this.valid, this.data, this.apiLink);
        this.submitting = true;
        this.api.submitByApiLink(this.apiLink, this.data, this.abortSignal)
            .then((response) => {
                this.submitSuccess = true;
                this.submitError = false;
                if (isNewApiObject(response.data)) {
                    this.navigateToNewResource(response.data.new);
                }
            })
            .catch(() => {
                this.submitError = true;
                this.submitSuccess = false;
            })
            .finally(() => {
                this.abortSignal = null;
                this.submitting = false;
            });
    }

    private navigateToNewResource(newResourceLink: ApiLink) {
        this.api.buildClientUrl(newResourceLink)
            .then(clientUrl => {
                this.router.navigate(`/explore/${clientUrl}`);
            });
    }
}
