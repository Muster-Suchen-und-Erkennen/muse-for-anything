import { bindable, bindingMode, observable } from "aurelia-framework";
import { NormalizedApiSchema, PropertyDescription } from "rest/schema-objects";
import { nanoid } from "nanoid";

export class ObjectForm {
    @bindable key: string;
    @bindable label: string;
    @bindable initialData: any;
    @bindable schema: NormalizedApiSchema;
    @bindable required: boolean = false;
    @bindable debug: boolean = false;
    @bindable valuePush: any;
    @bindable actions: Iterable<string>;
    @bindable actionSignal: unknown;
    @bindable({ defaultBindingMode: bindingMode.twoWay }) value: any;
    @bindable({ defaultBindingMode: bindingMode.fromView }) valid: boolean;
    @bindable({ defaultBindingMode: bindingMode.fromView }) dirty: boolean;

    isNullable: boolean = false;

    properties: PropertyDescription[] = [];
    propertiesByKey: Map<string, PropertyDescription> = new Map();
    requiredProperties: Set<string> = new Set();

    updateCount = 100;

    @observable() propertiesValid = {};
    @observable() propertiesDirty = {};

    hasExtraProperties: boolean = false;
    @observable() extraPropertyName: string = "";
    extraPropertyNameValid: boolean = false;
    allowedPatternPropertyKeys: RegExp[];

    slug = nanoid(8);

    invalidProps: string[];

    initialDataChanged(newValue, oldValue) {
        this.reloadProperties();
    }

    schemaChanged(newValue, oldValue) {
        this.valid = null;
        this.reloadProperties();
    }

    // eslint-disable-next-line complexity
    reloadProperties() {
        if (this.schema == null) {
            this.properties = [];
            this.requiredProperties = new Set();
            return;
        }
        if (this.schema.normalized.type == null || !this.schema.normalized.type.has("object")) {
            console.error("Not an object!"); // FIXME better error!
            this.properties = [];
            this.requiredProperties = new Set();
            return;
        }

        // check if nullable
        this.isNullable = this.schema.normalized.type.has("null");
        if (!this.isNullable && this.value == null) {
            window.setTimeout(() => {
                this.value = {};
            }, 1);
            return; // change in value will trigger reloadProperties again
        }

        // setup additionalProperties
        let hasAdditionalProperties = false;
        const additionalProperties = this.schema.normalized.additionalProperties;
        if (additionalProperties !== false && additionalProperties !== true) {
            hasAdditionalProperties = (additionalProperties as NormalizedApiSchema).normalized.mainType !== "any";
            this.allowedPatternPropertyKeys = null;
        } else {
            this.allowedPatternPropertyKeys = Array.from(this.schema.normalized.patternProperties?.keys() ?? []);
        }
        const hasPatternProperties = (this.schema.normalized.patternProperties?.size ?? 0) > 0;
        this.hasExtraProperties = hasAdditionalProperties || hasPatternProperties;

        // setup properties
        const currentData = { // TODO refactor to be less costly (maybe use set?)
            ...this.initialData,
            ...(this.value ?? {}),
        };
        const properties = this.schema.getPropertyList(Object.keys(currentData));
        const propertiesByKey = new Map<string, PropertyDescription>();
        properties.forEach(prop => {
            propertiesByKey.set(prop.propertyName, prop);
            if (prop.propertySchema.normalized.const !== undefined) {
                // pre set all const properties to be valid (workaround for update problems)
                this.propertiesValid[prop.propertyName] = true;
            }
        });
        this.properties = properties;
        this.propertiesByKey = propertiesByKey;
        this.requiredProperties = this.schema.normalized.required ?? new Set();

        if (this.hasExtraProperties) { // recheck valid status
            this.extraPropertyNameChanged(this.extraPropertyName);
        }
        this.updateSignal();
    }

    actionSignalCallback(action: { actionType: string, key: string }) {
        if (action.actionType === "remove" && this.value[action.key] !== undefined) {
            const newValue = { ...this.value };
            delete newValue[action.key];
            this.value = newValue;
        }
    }

    updateSignal() {
        window.setTimeout(() => {
            this.propertiesValidChanged(this.propertiesValid);
            this.propertiesDirtyChanged(this.propertiesDirty);
        }, 1);
    }

    editObject() {
        if (this.value == null) {
            this.value = {};
        }
    }

    valueChanged(newValue) {
        this.reloadProperties();
    }

    extraPropertyNameChanged(newValue) {
        if (newValue == null || newValue === "") {
            this.extraPropertyNameValid = false;
            return;
        }
        if (this.properties.some(prop => prop.propertyName === newValue)) {
            // property already present
            this.extraPropertyNameValid = false;
            return;
        }
        if (this.allowedPatternPropertyKeys != null) {
            // only patternProperties allowed
            if (this.allowedPatternPropertyKeys.some(regex => regex.test(newValue))) {
                this.extraPropertyNameValid = true;
                return;
            }
            this.extraPropertyNameValid = false;
            return;
        }
        this.extraPropertyNameValid = true;
    }

    addGhostProperty(propName: string) {
        if (this.value?.[propName] === undefined) {
            this.value = {
                ...(this.value ?? {}),
                [propName]: null,
            };
        }
    }

    addProperty() {
        if (!this.extraPropertyNameValid) {
            return;
        }
        const newProperty = this.schema.getPropertyList([this.extraPropertyName], { allowList: [this.extraPropertyName] });
        if (newProperty?.length === 1) {
            this.properties.push(newProperty[0]);
        }
        if (this.value == null) {
            this.value = {
                [this.extraPropertyName]: null,
            };
        }
        this.extraPropertyNameValid = false;
    }

    propertiesValidChanged(newValue: { [prop: string]: boolean }) {
        if (newValue == null) {
            this.valid = this.isNullable;
            return;
        }
        const propKeys = Object.keys(this.value ?? {});
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
            this.valid = allPropertiesValid;
            return;
        }
        const requiredPropKeys = propKeys.filter(key => this.requiredProperties.has(key));
        const allRequiredPresent = this.requiredProperties.size === requiredPropKeys.length;
        this.valid = allPropertiesValid && allRequiredPresent;
    }

    propertiesDirtyChanged(newValue: { [prop: string]: boolean }) {
        if (newValue == null) {
            this.dirty = false;
            return;
        }
        const propKeys = Object.keys(this.value ?? {});
        this.dirty = (propKeys.length === 0) || propKeys.some(key => newValue[key]);
    }
}
