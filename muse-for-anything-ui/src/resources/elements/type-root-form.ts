import { bindable, bindingMode, observable } from "aurelia-framework";
import { NormalizedApiSchema, PropertyDescription } from "rest/schema-objects";


export class TypeRootForm {
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

    typeSchema: NormalizedApiSchema;

    extraProperties: PropertyDescription[] = [];
    requiredProperties: Set<string> = new Set();

    @observable() propertiesValid = {};
    @observable() propertiesDirty = {};

    @observable() propertiesAreValid: boolean = false;
    @observable() propertiesAreDirty: boolean = false;

    invalidProps: string[];

    @observable() childSchemas = {};

    @observable() childSchemasValid = {};
    @observable() childSchemasDirty = {};

    @observable() childSchemasAreValid: boolean = false;
    @observable() childSchemasAreDirty: boolean = false;

    containedTypes: string[] = [];

    initialDataChanged(newValue, oldValue) {
        this.reloadProperties();
    }

    schemaChanged(newValue: NormalizedApiSchema, oldValue) {
        this.valid = null;
        this.typeSchema = newValue.normalized.properties?.get("definitions")?.normalized?.additionalProperties as NormalizedApiSchema;
        this.reloadProperties();
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
        const propertyBlockList = ["$schema", "$ref", "definitions", "$comment", "deprecated", "allOf"];
        this.extraProperties = this.schema.getPropertyList([], { // FIXME proper object keys...
            excludeReadOnly: true,
            blockList: propertyBlockList,
        });
        const normalized = this.schema.normalized;
        const requiredProperties = new Set(normalized.required);
        propertyBlockList.forEach(propKey => requiredProperties.delete(propKey));
        this.requiredProperties = requiredProperties;

        // calculate and apply default values
        const valueUpdate: any = {};
        const schemaRef = normalized.properties.get("$schema").normalized.const;
        if (this.value?.$schema !== schemaRef) {
            valueUpdate.$schema = schemaRef;
        }
        if (this.value?.$ref !== "#/definitions/root") {
            valueUpdate.$ref = "#/definitions/root";
        }
        if (this.value?.definitions == null) {
            valueUpdate.definitions = { root: {} };
        }
        if (valueUpdate || (this.value == null && this.required)) {
            window.setTimeout(() => {
                this.value = {
                    ...(this.value ?? {}),
                    ...valueUpdate,
                };
            }, 1);
        }
        this.updateSignal();
    }

    valueChanged(newValue, oldValue) {
        if (newValue == null) {
            if (this.required) {
                window.setTimeout(() => {
                    this.value = {
                        $schema: "http://json-schema.org/draft-07/schema#",
                        $ref: "#/definitions/root",
                        definitions: this.childSchemas,
                    };
                }, 1);
            }
            return;
        }
        const defs = newValue?.definitions;
        const containedTypes = Object.keys(defs).filter(t => t !== "root");
        containedTypes.sort();
        if (containedTypes.length !== this.containedTypes.length) {
            // different lengths
            this.containedTypes = containedTypes;
        } else if (containedTypes.some((t, i) => this.containedTypes[i] !== t)) {
            // different contents
            this.containedTypes = containedTypes;
        }
        if (newValue.definitions == null) {
            window.setTimeout(() => {
                this.value = {
                    ...newValue,
                    definitions: this.childSchemas,
                };
            }, 1);
        } else if (newValue.definitions !== this.childSchemas) {
            this.childSchemas = newValue.definitions;
        }
    }

    propertyActionSignal(action: { actionType: string, key: string }) {
        if (action.actionType === "remove" && this.value[action.key] !== undefined) {
            const newValue = { ...this.value };
            delete newValue[action.key];
            this.value = newValue;
        }
    }

    typeActionSignal(action: { actionType: string, key: string }) {
        if (action.actionType === "remove" && this.containedTypes.some(typeId => typeId === action.key)) {
            if (action.key === "root") {
                return; // never delete the root type
            }
            this.containedTypes = this.containedTypes.filter(typeId => typeId !== action.key);
            delete this.childSchemas[action.key];
            this.schemaUpdateSignal();
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

    addType() {
        if (this.value == null) {
            this.value = {
                $schema: "http://json-schema.org/draft-07/schema#",
                $ref: "#/definitions/root",
                definitions: this.childSchemas,
            };
        }
        let nextTypeId = 1;
        this.containedTypes.forEach(typeId => {
            if (/[0-9]+/.test(typeId)) {
                const nextId = Number(typeId) + 1;
                if (nextId > nextTypeId) {
                    nextTypeId = nextId;
                }
            }
        });
        this.containedTypes.push(nextTypeId.toString());
    }

    schemaUpdateSignal() {
        window.setTimeout(() => {
            this.childSchemasValidChanged(this.childSchemasValid);
            this.childSchemasDirtyChanged(this.childSchemasDirty);
        }, 1);
    }

    childSchemasValidChanged(newValue: { [prop: string]: boolean }) {
        const typesToCheck = ["root", ...(this.containedTypes ?? [])];
        this.childSchemasAreValid = typesToCheck.every(key => newValue[key]);
    }

    childSchemasDirtyChanged(newValue: { [prop: string]: boolean }) {
        const typesToCheck = ["root", ...(this.containedTypes ?? [])];
        this.childSchemasAreDirty = typesToCheck.some(key => newValue[key]);
    }

    updateSignal() {
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

    childSchemasAreValidChanged() {
        this.updateValid();
    }

    updateValid() {
        if (this.value == null) {
            this.valid = false; // this can never be nullable!
            return;
        }
        this.valid = this.propertiesAreValid && this.childSchemasAreValid;
    }

    propertiesAreDirtyChanged() {
        this.updateDirty();
    }

    childSchemasAreDirtyChanged() {
        this.updateDirty();

    }

    updateDirty() {
        this.dirty = this.propertiesAreDirty || this.childSchemasAreDirty;
    }
}
