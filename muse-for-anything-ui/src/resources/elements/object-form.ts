import { autoinject, bindable, bindingMode, observable, TaskQueue } from "aurelia-framework";
import { nanoid } from "nanoid";
import { NormalizedApiSchema, PropertyDescription } from "rest/schema-objects";

@autoinject
export class ObjectForm {
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
    @bindable({ defaultBindingMode: bindingMode.fromView }) valid: boolean;
    @bindable({ defaultBindingMode: bindingMode.fromView }) dirty: boolean;

    @observable() value: any = {};

    isNullable: boolean = false;

    properties: PropertyDescription[] = [];
    propertiesByKey: Map<string, PropertyDescription> = new Map();
    propertyState: { [prop: string]: "readonly" | "editable" | "missing" } = {};
    requiredProperties: Set<string> = new Set();

    updateCount = 100;

    deletedProperties = new Set<string>();

    @observable() propertiesValid = {};
    @observable() propertiesDirty = {};

    hasExtraProperties: boolean = false;
    @observable() extraPropertyName: string = "";
    extraPropertyNameValid: boolean = false;
    allowedPatternPropertyKeys: RegExp[];

    slug = nanoid(8);

    invalidProps: string[];

    private queue: TaskQueue;

    constructor(queue: TaskQueue) {
        this.queue = queue;
    }


    initialDataChanged(newValue, oldValue) {
        if (newValue != null && !this.value) {
            this.value = {}; // prime empty value for children to fill
        }
        this.deletedProperties.clear();
        this.reloadProperties();
    }

    schemaChanged(newValue, oldValue) {
        this.valid = null;
        if (this.value != null) {
            this.value = { ...(this.value ?? {}) };
        }
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
        const setProperties = new Set<string>();
        Object.keys(this.initialData ?? {}).forEach(key => {
            if (!this.deletedProperties.has(key)) {
                setProperties.add(key);
            }
        });
        if (this.value != null) {
            Object.keys(this.value).forEach(key => setProperties.add(key));
        }
        const properties = this.schema.getPropertyList(Array.from(setProperties.keys()));
        const propertiesByKey = new Map<string, PropertyDescription>();
        const propertyState: { [prop: string]: "readonly" | "editable" | "missing" } = {};
        const requiredProperties: Set<string> = this.schema.normalized.required ?? new Set();

        properties.forEach(prop => {
            propertiesByKey.set(prop.propertyName, prop);
            propertyState[prop.propertyName] = this.getPropertyState(prop, requiredProperties);
            if (prop.propertySchema.normalized.const !== undefined) {
                // TODO remove workaround issues
                // pre set all const properties to be valid (workaround for update problems)
                this.propertiesValid[prop.propertyName] = true;
            }
        });


        this.propertyState = propertyState;
        this.properties = properties;
        this.propertiesByKey = propertiesByKey;
        this.requiredProperties = requiredProperties;

        if (this.hasExtraProperties) { // recheck valid status
            this.extraPropertyNameChanged(this.extraPropertyName);
        }
        this.valueChanged(this.value);
    }

    actionSignalCallback(action: { actionType: string, key: string }) {
        if (action.actionType === "remove" && this.value[action.key] !== undefined) {
            const newValue = { ...this.value };
            delete newValue[action.key];
            this.value = newValue;
            // FIXME does not work correctly if iniial data still contains a value for te deleted property...
            this.deletedProperties.add(action.key);
            this.propertyState[action.key] = "missing";
            this.reloadProperties();
        } else {
            this.propertyState[action.key] = "missing";
            this.properties = this.properties.filter(prop => prop.propertyName !== action.key);
            if (this.hasExtraProperties) { // recheck valid status
                this.extraPropertyNameChanged(this.extraPropertyName);
            }
        }
    }

    editObject() {
        if (this.value == null) {
            this.value = {};
        }
    }

    valueInChanged(newValue) {
        if (newValue == null) {
            this.value = null;
        } else {
            this.value = { ...newValue };
        }
        this.reloadProperties();
    }

    onPropertyValueUpdate = (value, binding) => {
        this.queue.queueMicroTask(() => this.valueChanged(this.value));
    };

    valueChanged(newValue) {
        const newOutValue: any = {};
        let newValueIsDifferent = false;
        (this.properties ?? []).forEach(prop => {
            if (prop.propertySchema.normalized.readOnly) {
                return; // never output readonly properties
            }
            const key = prop.propertyName;
            if (newValue?.[key] !== undefined) {
                newOutValue[key] = newValue?.[key];
                if (prop.propertySchema.normalized.const !== undefined) {
                    // const values always win
                    newOutValue[key] = prop.propertySchema.normalized.const;
                }
                if (this.valueOut?.[key] !== newOutValue[key]) {
                    newValueIsDifferent = true;
                }
            }
        });
        const hasLessKeys = Object.keys(newOutValue).length < Object.keys(this.valueOut ?? {}).length;
        // FIXME console.log(newOutValue, newValueIsDifferent, hasLessKeys)
        if (newValueIsDifferent || hasLessKeys) {
            if (newValue == null && this.isNullable) {
                this.valueOut = null;
            } else {
                this.valueOut = newOutValue;
            }
        }
    }

    valueOutChanged(newValueOut) {
        Object.keys(newValueOut ?? {}).forEach(key => {
            if (newValueOut[key] != null) {
                this.deletedProperties.delete(key);
            }
        });
        this.queue.queueMicroTask(() => {
            this.propertiesValidChanged(this.propertiesValid);
            this.propertiesDirtyChanged(this.propertiesDirty);
        });
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

    addGhostProperty(propName: string) {
        if (this.value?.[propName] === undefined) {
            this.value = {
                ...(this.value ?? {}),
                [propName]: null,
            };
            this.propertyState[propName] = this.getPropertyState(this.propertiesByKey.get(propName));
        }
    }

    addProperty() {
        if (!this.extraPropertyNameValid) {
            return;
        }
        const newProperty = this.schema.getPropertyList([this.extraPropertyName], { allowList: [this.extraPropertyName] });
        if (newProperty?.length === 1) {
            this.propertyState[newProperty[0].propertyName] = "editable";
            this.properties.push(newProperty[0]);
        }
        if (this.value == null) {
            this.value = {
                [this.extraPropertyName]: null,
            };
        }
        this.extraPropertyNameValid = false;
    }

    onPropertyValidUpdate = (value, binding) => {
        this.queue.queueMicroTask(() => this.propertiesValidChanged(this.propertiesValid));
    };

    // eslint-disable-next-line complexity
    propertiesValidChanged(newValue: { [prop: string]: boolean }) {
        if (newValue == null) {
            this.valid = this.isNullable;
            return;
        }
        const propKeys = Object.keys(this.valueOut ?? {});
        const allPropertiesValid = propKeys.every(key => {
            if (newValue[key] != null) {
                return newValue[key]; // property validity is known
            }
            // assume valid if not required and not present
            return !this.requiredProperties.has(key) && this.valueOut[key] === undefined;
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

        let passwordFieldsMatch = true;
        if (this.valueOut?.password != null || this.valueOut?.retypePassword != null) {
            if (this.propertiesByKey.get("password").propertySchema?.normalized?.password
                && this.propertiesByKey.get("retypePassword").propertySchema?.normalized?.password) {
                passwordFieldsMatch = this.valueOut?.password === this.valueOut?.retypePassword;
                // TODO provide better feedback to user when passwords don't match
            }
        }

        this.valid = allPropertiesValid && allRequiredPresent && passwordFieldsMatch;
    }

    onPropertyDirtyUpdate = (value, binding) => {
        this.queue.queueMicroTask(() => this.propertiesDirtyChanged(this.propertiesDirty));
    };

    propertiesDirtyChanged(newValue: { [prop: string]: boolean }) {
        if (newValue == null) {
            this.dirty = false;
            return;
        }
        const propKeys = Object.keys(this.valueOut ?? {});
        this.dirty = (propKeys.length === 0) || propKeys.some(key => newValue[key]);
    }
}
