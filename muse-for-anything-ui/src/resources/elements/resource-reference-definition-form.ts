import { DialogService } from "aurelia-dialog";
import { autoinject, bindable, bindingMode, observable, TaskQueue } from "aurelia-framework";
import { ApiLink } from "rest/api-objects";
import { BaseApiService } from "rest/base-api";
import { NormalizedApiSchema, PropertyDescription } from "rest/schema-objects";
import { ApiObjectChooserDialog } from "./api-object-chooser-dialog";


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
    @bindable({ defaultBindingMode: bindingMode.toView }) valueIn: any;
    @bindable({ defaultBindingMode: bindingMode.fromView }) valueOut: any;
    @bindable({ defaultBindingMode: bindingMode.fromView }) dirty: boolean;
    @bindable({ defaultBindingMode: bindingMode.fromView }) valid: boolean;

    @observable() value: any = {};

    extraProperties: PropertyDescription[] = [];
    propertyState: { [prop: string]: "readonly" | "editable" | "missing" } = {};
    requiredProperties: Set<string> = new Set();

    @observable() propertiesValid = {};
    @observable() propertiesDirty = {};

    @observable() propertiesAreValid: boolean = false;
    @observable() propertiesAreDirty: boolean = false;

    currentReferenceValid = false;

    invalidProps: string[];

    currentReferenceType: string;
    namespaceApiLink: ApiLink;

    currentResourceLink: ApiLink;

    private dialogService: DialogService;
    private apiService: BaseApiService;
    private queue: TaskQueue;

    constructor(dialogService: DialogService, apiService: BaseApiService, queue: TaskQueue) {
        this.dialogService = dialogService;
        this.apiService = apiService;
        this.queue = queue;
    }

    initialDataChanged(newValue, oldValue) {
        if (newValue != null) {
            const initialValue: any = {};
            if (newValue.referenceType != null) {
                initialValue.referenceType = newValue.referenceType;
                this.currentReferenceType = newValue.referenceType;
            }
            if (newValue.referenceKey != null) {
                initialValue.referenceKey = newValue.referenceKey;
                // TODO calc reference key…
            }
            this.value = initialValue; // prime new value for children to fill
        }
        this.reloadProperties();
    }

    schemaChanged(newValue: NormalizedApiSchema, oldValue) {
        this.valid = null;
        if (this.value != null) {
            this.value = { ...(this.value ?? {}) };
        }
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
        if (!this.schema.normalized.type?.has("object")) {
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
        const propertyState: { [prop: string]: "readonly" | "editable" | "missing" } = {};
        this.extraProperties.forEach(prop => {
            propertyState[prop.propertyName] = this.getPropertyState(prop, requiredProperties);
        });
        this.propertyState = propertyState;
        propertyBlockList.forEach(propKey => requiredProperties.delete(propKey));
        this.requiredProperties = requiredProperties;

        this.valueChanged(this.value, null);
    }

    valueInChanged(newValue) {
        if (newValue == null) {
            this.value = {}; // is never nullable!
        } else {
            this.currentReferenceType = newValue.referenceType ?? "ont-taxonomy";
            this.value = { ...newValue };
            // TODO calc reference link…
        }
        this.reloadProperties();

        // defer a update valid until after value settles
        this.queue.queueMicroTask(() => this.updateValid());
    }

    onPropertyValueUpdate = (value, binding) => {
        this.valueChanged(this.value, null);
    };

    valueChanged(newValue, oldValue) {
        this.checkReferenceType();
        this.checkReferenceLink();
        const newValueOut: any = {}; // TODO
        this.extraProperties?.forEach(prop => {
            if (newValue?.[prop.propertyName] !== undefined) {
                newValueOut[prop.propertyName] = newValue[prop.propertyName];
            }
        });
        newValueOut.referenceKey = newValue?.referenceKey ?? null;
        if (newValueOut.customType !== "resourceReference") {
            newValueOut.customType = "resourceReference";
        }
        if (newValueOut.type == null) {
            newValueOut.type = ["object"];
        }
        if (newValueOut.required == null) {
            newValueOut.required = ["referenceType", "referenceKey"];
        }

        const refType = newValueOut.referenceType ?? "ont-type";
        let childRefType = "ont-object";
        if (refType === "ont-type") {
            childRefType = "ont-object";
        }
        if (refType === "ont-taxonomy") {
            childRefType = "ont-taxonomy-item";
        }
        if (newValueOut.properties == null || newValueOut.properties?.referenceType?.const !== childRefType) {
            newValueOut.properties = {
                referenceType: { const: childRefType },
                referenceKey: {
                    type: "object",
                    additionalProperties: { type: "string", singleLine: true },
                },
            };
        }

        if (newValueOut.referenceKey == null) {
            delete newValueOut.referenceKey;
        }

        // todo: fix frequent updates?
        this.valueOut = newValueOut;
    }

    valueOutChanged() {
        this.propertiesValidChanged(this.propertiesValid);
        this.propertiesDirtyChanged(this.propertiesDirty);
        this.updateValid();
    }

    checkReferenceType() {
        // TODO change resource type?
        if (this.currentReferenceType !== this.value?.referenceType) {
            if (this.currentReferenceType != null && this.value != null) {
                // delete current key as it is for a different ref type
                const valuematchesValueIn = this.valueIn?.referenceKey === this.value.referenceKey && this.valueIn?.referenceType === this.value.referenceType;
                const referenceTypeMatchesInitialData = this.initialData?.referenceType === this.value.referenceType;
                const valueMatchesInitialData = this.initialData?.referenceKey === this.value.referenceKey && referenceTypeMatchesInitialData;
                if (!(valuematchesValueIn || valueMatchesInitialData)) {
                    // but only if it does not match valueIn or initialData
                    this.value.referenceKey = null; // TODO save for reuse?
                }
                if (referenceTypeMatchesInitialData && this.value.referenceKey == null) {
                    // restore initial data reference key if switching to a reference type matching initial data
                    this.value.referenceKey = this.initialData?.referenceKey;
                }
            }
            this.currentReferenceType = this.value?.referenceType;
        }
    }

    checkReferenceLink() {
        if (this.value.referenceKey == null) {
            this.currentResourceLink = null;
        } else {
            if (Object.keys(this.value.referenceKey).some(key => this.currentResourceLink?.resourceKey?.[key] !== this.value.referenceKey[key])) {
                // reload reference link…
                this.apiService.resolveLinkKey(this.value.referenceKey, this.currentReferenceType).then(links => {
                    this.currentResourceLink = links.find(link => !link.rel.some(rel => rel === "collection"));
                });
            }
        }
    }

    private showAddPropertyButton(prop: PropertyDescription, requiredProperties: Set<string>): boolean {
        const hasNoInitialValue = this.initialData?.[prop.propertyName] === undefined;
        const hasNoValue = this.value?.[prop.propertyName] === undefined && !(prop.propertySchema.normalized.readOnly);
        const isNotRequired = !requiredProperties.has(prop.propertyName);
        return hasNoValue && hasNoInitialValue && isNotRequired;
    }

    private showReadOnlyProp(prop: PropertyDescription): boolean {
        const isReadOnly = prop.propertySchema.normalized.readOnly;
        const hasInitialValue = this.initialData?.[prop.propertyName] !== undefined;
        return isReadOnly && hasInitialValue;
    }

    private showPropertyForm(prop: PropertyDescription): boolean {
        const isReadOnly = prop.propertySchema.normalized.readOnly;
        const hasInitialValue = this.initialData?.[prop.propertyName] !== undefined;
        const hasValue = this.value?.[prop.propertyName] !== undefined;
        return !isReadOnly && (hasInitialValue || hasValue);
    }

    getPropertyState(prop: PropertyDescription, requiredProperties?: Set<string>): "readonly" | "editable" | "missing" {
        const requiredProps = requiredProperties ?? this.requiredProperties ?? new Set<string>();
        if (this.showAddPropertyButton(prop, requiredProps)) {
            return "missing";
        }
        if (this.showReadOnlyProp(prop)) {
            return "readonly";
        }
        if (this.showPropertyForm(prop)) {
            return "editable";
        }
        return "editable";
    }

    propertyActionSignal(action: { actionType: string, key: string }) {
        if (action.actionType === "remove" && this.value[action.key] !== undefined) {
            const newValue = { ...this.value };
            delete newValue[action.key];
            this.value = newValue;
            this.propertyState[action.key] = "missing";
        }
    }

    addGhostProperty(propName: string) {
        if (this.value?.[propName] === undefined) {
            this.value = {
                ...(this.value ?? {}),
                [propName]: null,
            };
            const prop = this.extraProperties.find(prop => prop.propertyName === propName);
            if (prop != null) {
                this.propertyState[propName] = this.getPropertyState(prop);
            } else {
                this.propertyState[propName] = "editable";
            }
        }
    }

    onPropertyValidUpdate = (value, binding) => {
        this.propertiesValidChanged(this.propertiesValid);
    };

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
            return !this.requiredProperties.has(key) && this.valueOut?.[key] === undefined;
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

    onPropertyDirtyUpdate = (value, binding) => {
        this.propertiesDirtyChanged(this.propertiesDirty);
    };

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
        if (this.valueOut == null) {
            this.valid = false; // this can never be nullable!
            return;
        }
        let referenceKeyValid = false;
        if (this.currentReferenceType === "ont-type") {
            referenceKeyValid = true;
        }
        if (this.currentReferenceType === "ont-taxonomy") {
            referenceKeyValid = this.valueOut.referenceKey != null;
        }
        this.currentReferenceValid = referenceKeyValid;
        this.valid = this.propertiesAreValid && referenceKeyValid;
    }

    propertiesAreDirtyChanged() {
        this.updateDirty();
    }


    updateDirty() {
        this.dirty = this.propertiesAreDirty;
    }

    openResourceChooser() {
        if (this.currentReferenceType == null || this.namespaceApiLink == null) {
            return;
        }
        const model = {
            referenceType: this.currentReferenceType,
            baseApiLink: this.namespaceApiLink,
        };
        this.dialogService.open({ viewModel: ApiObjectChooserDialog, model: model, lock: false }).whenClosed(response => {
            if (!response.wasCancelled) {
                if (this.value == null || this.currentReferenceType !== model.referenceType) {
                    return;
                }
                this.value.referenceKey = (response.output as ApiLink).resourceKey;
                this.currentResourceLink = (response.output as ApiLink);
                this.valueChanged(this.value, null);
            } else {
                // do nothing on cancel
            }
        });
    }
}
