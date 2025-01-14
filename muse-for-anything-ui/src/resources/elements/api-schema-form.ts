import { bindable, autoinject, observable, bindingMode } from "aurelia-framework";
import { EventAggregator } from "aurelia-event-aggregator";
import { Router } from "aurelia-router";
import { BindingSignaler } from "aurelia-templating-resources";
import { ApiLink, isApiObject, isChangedApiObject, isNewApiObject } from "rest/api-objects";
import { BaseApiService } from "rest/base-api";
import { NormalizedApiSchema } from "rest/schema-objects";
import { SchemaService } from "rest/schema-service";
import { API_RESOURCE_CHANGES_CHANNEL } from "resources/events";

@autoinject
export class ApiSchemaForm {
    @bindable autoNavigate: boolean = true;
    @bindable initialData;
    @bindable apiLink: ApiLink;
    @bindable context: any;
    @bindable debug: boolean = false;
    @bindable valuePush: any;
    @bindable({ defaultBindingMode: bindingMode.twoWay }) data: any;
    @bindable({ defaultBindingMode: bindingMode.fromView }) valid: boolean;
    @bindable({ defaultBindingMode: bindingMode.fromView }) submitting: boolean = false;
    @bindable({ defaultBindingMode: bindingMode.fromView }) abortSignal: AbortSignal;
    @bindable({ defaultBindingMode: bindingMode.fromView }) submitSuccess: boolean = false;
    @bindable({ defaultBindingMode: bindingMode.fromView }) submitError: boolean = false;
    @bindable({ defaultBindingMode: bindingMode.fromView }) errorMessage: string = "";

    @observable schema: NormalizedApiSchema;
    resourceTypeTranslationKey: string;


    private api: BaseApiService;
    private schemaService: SchemaService;

    private bindingSignaler: BindingSignaler;
    private router: Router;
    private events: EventAggregator;

    constructor(schemaService: SchemaService, basApi: BaseApiService, bindingSingaler: BindingSignaler, router: Router, events: EventAggregator) {
        this.schemaService = schemaService;
        this.api = basApi;

        this.bindingSignaler = bindingSingaler;
        this.router = router;
        this.events = events;
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
        if (this.debug) {
            console.info("New Schema", newValue);
        }
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
        console.log(JSON.stringify(this.data))
        this.errorMessage = "";
        this.submitting = true;
        this.api.submitByApiLink(this.apiLink, this.data, this.abortSignal)
            .then((response) => {
                this.submitSuccess = true;
                this.submitError = false;
                if (isNewApiObject(response.data)) {
                    this.navigateToNewResource(response.data.new);
                }
                if (isChangedApiObject(response.data)) {
                    this.navigateToChangedResource(response.data.changed);
                    this.events.publish(API_RESOURCE_CHANGES_CHANNEL, response.data.changed.resourceKey);
                }
            })
            .catch((error) => {
                this.submitError = true;
                this.submitSuccess = false;
                if (error.response && error.response.status === 400) {
                    this.errorMessage = "Schema change is invalid";
                }
            })
            .finally(() => {
                this.abortSignal = null;
                this.submitting = false;
            });
    }

    private navigateToNewResource(newResourceLink: ApiLink) {
        if (this.autoNavigate) {
            this.api.buildClientUrl(newResourceLink)
                .then(clientUrl => {
                    this.router.navigate(`/explore/${clientUrl}`);
                });
        }
    }

    private navigateToChangedResource(changedResourceLink: ApiLink) {
        if (this.autoNavigate) {
            this.api.buildClientUrl(changedResourceLink)
                .then(clientUrl => {
                    this.router.navigate(`/explore/${clientUrl}`);
                });
        }
    }
}
