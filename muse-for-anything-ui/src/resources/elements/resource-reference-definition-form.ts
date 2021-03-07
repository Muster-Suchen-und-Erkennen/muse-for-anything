import { bindable, bindingMode, observable, autoinject } from "aurelia-framework";
import { DialogService } from "aurelia-dialog";
import { NormalizedApiSchema, PropertyDescription } from "rest/schema-objects";
import { ApiObjectChooserDialog } from "./api-object-chooser-dialog";
import { BaseApiService } from "rest/base-api";
import { ApiLink } from "rest/api-objects";


@autoinject()
export class ResourceReferenceDefinitionForm {
    @bindable key: string;
    @bindable label: string;
    @bindable initialData: any;
    @bindable schema: NormalizedApiSchema;
    @bindable required: boolean = false;
    @bindable debug: boolean = false;
    @bindable context: any;
    @bindable valuePush: any;
    @bindable actions: Iterable<string>;
    @bindable actionSignal: unknown;
    @bindable({ defaultBindingMode: bindingMode.twoWay }) value: any;
    @bindable({ defaultBindingMode: bindingMode.fromView }) dirty: boolean;
    @bindable({ defaultBindingMode: bindingMode.fromView }) valid: boolean;

    extraProperties: PropertyDescription[] = [];
    requiredProperties: Set<string> = new Set();

    @observable() propertiesValid = {};
    @observable() propertiesDirty = {};

    @observable() propertiesAreValid: boolean = false;
    @observable() propertiesAreDirty: boolean = false;

    invalidProps: string[];

    referenceType: string;
    namespaceApiLink: ApiLink;

    currentResourceLink: ApiLink;

    private dialogService: DialogService;
    private apiService: BaseApiService;

    constructor(dialogService: DialogService, apiService: BaseApiService) {
        this.dialogService = dialogService;
        this.apiService = apiService;
    }

    initialDataChanged(newValue, oldValue) {
        this.reloadProperties();
    }

    schemaChanged(newValue: NormalizedApiSchema, oldValue) {
        this.valid = null;
        this.reloadProperties();
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
    }

    // eslint-disable-next-line complexity
    reloadProperties() {
        if (this.schema == null) {
            this.extraProperties = [];
            this.requiredProperties = new Set();
            return;
        }
        if (!this.schema.normalized.type.has("object")) {
            console.error("Not an object!"); // FIXME better error!
            this.extraProperties = [];
            this.requiredProperties = new Set();
            return;
        }
        const propertyBlockList = ["$comment", "deprecated", "required", "customType", "referenceKey", "properties"];
        this.extraProperties = this.schema.getPropertyList([], { // FIXME proper object keys...
            excludeReadOnly: true,
            blockList: propertyBlockList,
        });
        const normalized = this.schema.normalized;
        const requiredProperties = new Set(normalized.required);
        propertyBlockList.forEach(propKey => requiredProperties.delete(propKey));
        this.requiredProperties = requiredProperties;

        this.fixValue();
        this.updateSignal();
    }

    // eslint-disable-next-line complexity
    private fixValue() {
        // calculate and apply default values
        const valueUpdate: any = {};
        if (this.value?.customType !== "resourceReference") {
            valueUpdate.customType = "resourceReference";
        }
        if (this.value?.type == null) {
            valueUpdate.type = ["object"];
        }
        if (this.value?.required == null) {
            valueUpdate.required = ["referenceType", "referenceKey"];
        }

        const refType = this.value?.referenceType ?? "ont-type";
        let childRefType = "ont-object";
        if (refType === "ont-type") {
            childRefType = "ont-object";
        }
        if (refType === "ont-taxonomy") {
            childRefType = "ont-taxonomy-item";
        }
        if (this.value?.properties == null || this.value?.properties?.referenceType?.const !== childRefType) {
            valueUpdate.properties = {
                referenceType: { const: childRefType },
                referenceKey: {
                    type: "object",
                    additionalProperties: { type: "string", singleLine: true },
                },
            };
        }

        if (Object.keys(valueUpdate).length > 0 || (this.value == null && this.required)) {
            window.setTimeout(() => { // FIXME this trigger very often...
                this.value = {
                    ...(this.value ?? {}),
                    ...valueUpdate,
                };
            }, 1);
        }
    }

    valueChanged(newValue, oldValue) {
        this.fixValue();
        this.checkReferenceType();
    }

    checkReferenceType() {
        // TODO change resource type?
        if (this.referenceType !== this.value?.referenceType) {
            this.value.referenceKey = null; // TODO save for reuse?
            this.referenceType = this.value?.referenceType;
            this.updateValid();
        }
    }

    propertyActionSignal(action: { actionType: string, key: string }) {
        if (action.actionType === "remove" && this.value[action.key] !== undefined) {
            const newValue = { ...this.value };
            delete newValue[action.key];
            this.value = newValue;
        }
    }

    addGhostProperty(propName: string) {
        if (this.value?.[propName] === undefined) {
            this.value = {
                ...(this.value ?? {}),
                [propName]: null,
            };
        }
    }

    updateSignal() {
        this.checkReferenceType();
        this.fixValue();
        window.setTimeout(() => {
            this.propertiesValidChanged(this.propertiesValid);
            this.propertiesDirtyChanged(this.propertiesDirty);
        }, 1);
    }

    propertiesValidChanged(newValue: { [prop: string]: boolean }) {
        if (newValue == null) {
            this.propertiesAreValid = !this.required;
            return;
        }
        const propKeys = this.extraProperties.map(prop => prop.propertyName);
        const allPropertiesValid = propKeys.every(key => {
            if (newValue[key] != null) {
                return newValue[key]; // property validity is known
            }
            // assume valid if not required and not present
            return !this.requiredProperties.has(key) && this.value[key] === undefined;
        });
        if (!allPropertiesValid) {
            this.invalidProps = propKeys.filter(key => !newValue[key]);
        } else {
            this.invalidProps = [];
        }
        if (this.requiredProperties == null || this.requiredProperties.size === 0) {
            this.propertiesAreValid = allPropertiesValid;
            return;
        }
        const requiredPropKeys = propKeys.filter(key => this.requiredProperties.has(key));
        const allRequiredPresent = this.requiredProperties.size === requiredPropKeys.length;
        this.propertiesAreValid = allPropertiesValid && allRequiredPresent;
    }

    propertiesDirtyChanged(newValue: { [prop: string]: boolean }) {
        if (newValue == null) {
            this.propertiesAreDirty = false;
            return;
        }
        const propKeys = this.extraProperties.map(prop => prop.propertyName);
        this.propertiesAreDirty = (propKeys.length === 0) || propKeys.some(key => newValue[key]);
    }

    propertiesAreValidChanged() {
        this.updateValid();
    }


    updateValid() {
        if (this.value == null) {
            this.valid = false; // this can never be nullable!
            return;
        }
        let referenceKeyValid = false;
        if (this.referenceType === "ont-type") {
            referenceKeyValid = true;
        }
        if (this.referenceType === "ont-taxonomy") {
            referenceKeyValid = this.value.referenceKey != null;
        }
        this.valid = this.propertiesAreValid && referenceKeyValid;
    }

    propertiesAreDirtyChanged() {
        this.updateDirty();
    }


    updateDirty() {
        this.dirty = this.propertiesAreDirty;
    }

    openResourceChooser() {
        if (this.referenceType == null || this.namespaceApiLink == null) {
            return;
        }
        const model = {
            referenceType: this.referenceType,
            baseApiLink: this.namespaceApiLink,
        };
        this.dialogService.open({ viewModel: ApiObjectChooserDialog, model: model, lock: false }).whenClosed(response => {
            if (!response.wasCancelled) {
                if (this.value == null || this.referenceType !== model.referenceType) {
                    return;
                }
                this.value.referenceKey = (response.output as ApiLink).resourceKey;
                this.currentResourceLink = (response.output as ApiLink);
                this.updateValid();
            } else {
                // do nothing on cancel
            }
        });
    }
}
