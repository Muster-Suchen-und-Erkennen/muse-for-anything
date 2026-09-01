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
    @bindable({ defaultBindingMode: bindingMode.toView }) valueIn: { referenceType: string, referenceKey: ApiLinkKey };
    @bindable({ defaultBindingMode: bindingMode.fromView }) valueOut: { referenceType: string, referenceKey: ApiLinkKey };
    @bindable({ defaultBindingMode: bindingMode.fromView }) dirty: boolean;
    @bindable({ defaultBindingMode: bindingMode.fromView }) valid: boolean;

    showInfo: boolean = false;

    description: string = "";

    referenceRootType: string;
    referenceRootKey: ApiLinkKey;

    isNullable: boolean = false;

    isCurrentlyNull: boolean = false;

    @observable() currentReferenceType: string;
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

    toggleInfo() {
        this.showInfo = !this.showInfo;
        return false;
    }

    initialDataChanged(newValue, oldValue) {
        if (newValue != null) {
            this.currentReferenceType = newValue.referenceType;
            this.currentReferenceKey = newValue.referenceKey;
        } else {
            this.isCurrentlyNull = true;
            this.updateValueOut();
        }
    }

    schemaChanged(newValue: NormalizedApiSchema, oldValue) {
        this.valid = null;
        this.referenceRootType = null;
        this.referenceRootKey = null;
        this.description = "";

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
            this.isNullable = schema.type?.has("null") ?? false;
            this.referenceRootType = schema.referenceType;
            this.referenceRootKey = schema.referenceKey;
            this.currentReferenceType = refType;
            this.description = schema.description ?? "";
            this.updateValueOut();
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

    valueInChanged(newValue) {
        if (newValue != null) {
            this.currentReferenceType = newValue.referenceType;
            this.currentReferenceKey = newValue.referenceKey;
        } else {
            this.isCurrentlyNull = true;
            this.updateValueOut();
        }
    }

    currentReferenceTypeChanged(newValue: string) {
        this.updateValueOut();
    }

    currentReferenceKeyChanged(newValue: ApiLinkKey) {
        this.updateValueOut();
        if (newValue == null && this.currentResourceLink != null) {
            this.currentResourceLink = null;
            return;
        }
        if (Object.keys(newValue ?? {}).every(key => newValue[key] === this.currentResourceLink?.resourceKey?.[key])) {
            return; // link key matches
        }

        // link key does not match, find new link
        this.apiService.resolveLinkKey(newValue, this.currentReferenceType).then(results => {
            this.currentResourceLink = results.find(link => !link.rel.some(rel => rel === "collection"));
        });
    }

    updateValueOut() {
        if (this.isCurrentlyNull && this.valueOut !== null) {
            this.valueOut = null;
            return;
        }
        if (this.valueOut?.referenceKey === this.currentReferenceKey && this.valueOut?.referenceType === this.currentReferenceType) {
            return;
        }
        this.valueOut = {
            referenceType: this.currentReferenceType,
            referenceKey: this.currentReferenceKey,
        };
    }

    valueOutChanged(newValue) {
        this.updateValid();
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
    }



    updateValid() {
        if (this.valueOut == null) {
            this.valid = this.isNullable;
            return;
        }
        let referenceKeyValid = false;
        if (this.currentReferenceType === "ont-object") {
            referenceKeyValid = this.valueOut?.referenceType === "ont-object" && this.valueOut.referenceKey != null;
        }
        if (this.currentReferenceType === "ont-taxonomy-item") {
            referenceKeyValid = this.valueOut?.referenceType === "ont-taxonomy-item" && this.valueOut.referenceKey != null;
        }
        this.valid = referenceKeyValid;
    }

    openResourceChooser() {
        if (this.currentReferenceType == null || this.namespaceApiLink == null) {
            return;
        }
        const model = {
            referenceType: this.currentReferenceType,
            baseApiLink: this.referenceRootApiLink ?? this.namespaceApiLink,
        };
        this.dialogService.open({ viewModel: ApiObjectChooserDialog, model: model, lock: false }).whenClosed(response => {
            if (!response.wasCancelled) {
                if (this.currentReferenceType !== model.referenceType) {
                    return;
                }
                this.currentReferenceKey = (response.output as ApiLink).resourceKey;
            } else {
                // do nothing on cancel
            }
        });
    }
}
