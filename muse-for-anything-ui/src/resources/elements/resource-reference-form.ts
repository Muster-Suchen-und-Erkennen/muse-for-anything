import { bindable, bindingMode, observable, autoinject } from "aurelia-framework";
import { DialogService } from "aurelia-dialog";
import { NormalizedApiSchema, PropertyDescription } from "rest/schema-objects";
import { ApiObjectChooserDialog } from "./api-object-chooser-dialog";
import { BaseApiService } from "rest/base-api";
import { ApiLink, ApiLinkKey } from "rest/api-objects";


@autoinject()
export class ResourceReferenceForm {
    @bindable key: string;
    @bindable label: string;
    @bindable initialData: { referenceType?: string, referenceKey?: ApiLinkKey };
    @bindable schema: NormalizedApiSchema;
    @bindable required: boolean = false;
    @bindable debug: boolean = false;
    @bindable context: { baseApiLink?: ApiLink };
    @bindable valuePush: any;
    @bindable actions: Iterable<string>;
    @bindable actionSignal: unknown;
    @bindable({ defaultBindingMode: bindingMode.twoWay }) value: { referenceType: string, referenceKey: ApiLinkKey };
    @bindable({ defaultBindingMode: bindingMode.fromView }) dirty: boolean;
    @bindable({ defaultBindingMode: bindingMode.fromView }) valid: boolean;

    referenceRootType: string;
    referenceRootKey: ApiLinkKey;

    referenceType: string;

    currentReferenceType: string;
    @observable() currentReferenceKey: ApiLinkKey;

    namespaceApiLink: ApiLink;
    referenceRootApiLink: ApiLink;

    currentResourceLink: ApiLink;

    private dialogService: DialogService;
    private apiService: BaseApiService;

    constructor(dialogService: DialogService, apiService: BaseApiService) {
        this.dialogService = dialogService;
        this.apiService = apiService;
    }

    initialDataChanged(newValue, oldValue) {
        // todo copy value
        this.updateValid();
    }

    schemaChanged(newValue: NormalizedApiSchema, oldValue) {
        this.valid = null;
        this.referenceRootType = null;
        this.referenceRootKey = null;

        if (newValue != null) {
            const schema = newValue.normalized;
            const refType = schema.properties.get("referenceType")?.normalized?.const as string; // TODO proper type checking?
            if (schema.referenceType === "ont-taxonomy") {
                if (refType !== "ont-taxonomy-item") {
                    // TODO better warnings/error handling
                    console.warn("Unknown reference definition encountered.");
                }
            }
            if (schema.referenceType === "ont-taxonomy") {
                if (refType !== "ont-taxonomy-item") {
                    // TODO better warnings/error handling
                    console.warn("Unknown reference definition encountered.");
                }
            }
            this.referenceRootType = schema.referenceType;
            this.referenceRootKey = schema.referenceKey;
            this.referenceType = refType;
        }
        this.reloadReferenceRoot();
    }

    contextChanged(newValue, oldValue) {
        if (newValue?.baseApiLink?.href === oldValue?.baseApiLink?.href) {
            return;
        }
        this.namespaceApiLink = null;
        if (newValue?.baseApiLink == null) {
            return;
        }

        this.apiService.getByApiLink(newValue?.baseApiLink).then(response => {
            this.namespaceApiLink = response.links.find(link => {
                if (link.resourceType !== "ont-namespace") {
                    return false;
                }
                if (link.rel.some(rel => rel === "collection")) {
                    return false;
                }
                if (link.rel.some(rel => rel === "nav" || rel === "up")) {
                    return true;
                }
                return false;
            });
        });

        // TODO
        this.reloadReferenceRoot();
    }

    currentReferenceKeyChanged(newValue: ApiLinkKey) {
        if (newValue === this.value?.referenceKey) {
            return;
        }
        console.log(newValue)
        this.value = {
            referenceType: this.referenceType,
            referenceKey: newValue,
        };

        console.log(newValue)

        this.apiService.resolveLinkKey(newValue, this.referenceType).then(results => {
            this.currentResourceLink = results.find(link => !link.rel.some(rel => rel === "collection"));
        });
    }

    reloadReferenceRoot() {
        if (this.referenceRootType == null) {
            return;
        }

        if (this.context?.baseApiLink == null) {
            return;
        }

        const key = this.referenceRootKey ?? this.context.baseApiLink.resourceKey;
        const keyLength = Object.keys(key).length;

        this.apiService.resolveLinkKey(key, this.referenceRootType).then(links => {
            this.referenceRootApiLink = links.find(link => !link.rel.some(rel => rel === "collection"));
        });

        this.fixValue();

    }

    // eslint-disable-next-line complexity
    private fixValue() {
        const valueUpdate = null;

        // TODO change value if invalid?
        //if (Object.keys(valueUpdate).length > 0 || (this.value == null && this.required)) {
        //    window.setTimeout(() => { // FIXME this trigger very often...
        //        this.value = {
        //            ...(this.value ?? {}),
        //            ...valueUpdate,
        //        };
        //    }, 1);
        //}
    }

    valueChanged(newValue, oldValue) {
        this.fixValue();
        this.updateValid();
    }

    updateValid() {
        if (this.value == null) {
            this.valid = false; // this can never be nullable!
            return;
        }
        let referenceKeyValid = false;
        if (this.referenceType === "ont-object") {
            referenceKeyValid = this.value?.referenceType === "ont-object" && this.value.referenceKey != null;
        }
        if (this.referenceType === "ont-taxonomy-item") {
            referenceKeyValid = this.value?.referenceType === "ont-taxonomy-item" && this.value.referenceKey != null;
        }
        this.valid = referenceKeyValid;
    }

    openResourceChooser() {
        if (this.referenceType == null || this.namespaceApiLink == null) {
            return;
        }
        const model = {
            referenceType: this.referenceType,
            baseApiLink: this.referenceRootApiLink ?? this.namespaceApiLink,
        };
        this.dialogService.open({ viewModel: ApiObjectChooserDialog, model: model, lock: false }).whenClosed(response => {
            if (!response.wasCancelled) {
                if (this.referenceType !== model.referenceType) {
                    return;
                }
                this.currentReferenceKey = (response.output as ApiLink).resourceKey;
            } else {
                // do nothing on cancel
            }
        });
    }
}
