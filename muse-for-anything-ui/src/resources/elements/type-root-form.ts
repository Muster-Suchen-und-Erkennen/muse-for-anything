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
    @bindable({ defaultBindingMode: bindingMode.toView }) valueIn: any;
    @bindable({ defaultBindingMode: bindingMode.fromView }) valueOut: any;
    @bindable({ defaultBindingMode: bindingMode.fromView }) dirty: boolean;
    @bindable({ defaultBindingMode: bindingMode.fromView }) valid: boolean;

    @observable value: any = {};

    typeSchema: NormalizedApiSchema;

    extraProperties: PropertyDescription[] = [];
    requiredProperties: Set<string> = new Set();

    @observable() propertiesValid = {};
    @observable() propertiesDirty = {};

    invalidProps: string[];

    @observable() childSchemas: any = {};

    @observable() childSchemasValid = {};
    @observable() childSchemasDirty = {};

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
        this.valueChanged(this.value, null);
    }


    valueInChanged(newValue) {
        if (newValue == null) {
            return;
        }

        const value = { ...newValue };
        this.childSchemas = { ...(value?.definitions ?? {}) };
        delete value.definitions;
        this.value = value;

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

    }

    onPropertyValueUpdate = (value, binding) => {
        this.valueChanged(this.value, null);
    };

    onSchemaValueUpdate = (value, binding) => {
        this.valueChanged(this.value, null);
    };

    valueChanged(newValue, oldValue) {

        if (newValue == null) {
            if (this.required) {
                this.valueOut = {
                    $schema: "http://json-schema.org/draft-07/schema#",
                    $ref: "#/definitions/root",
                    definitions: { root: this.childSchemas?.root ?? {} },
                };
            } else {
                this.valueOut = null;
            }
            return;
        }

        const newValueOut: any = { ...newValue };

        const normalized = this.schema?.normalized;
        const schemaRef = normalized?.properties?.get("$schema")?.normalized?.const ?? "";
        if (newValueOut?.$schema !== schemaRef) {
            newValueOut.$schema = schemaRef;
        }
        if (newValueOut?.$ref !== "#/definitions/root") {
            newValueOut.$ref = "#/definitions/root";
        }
        newValueOut.definitions = {
            root: this.childSchemas?.root ?? {},
        };
        this.containedTypes?.forEach(schema => {
            newValueOut.definitions[schema] = this.childSchemas?.[schema];
        });

        // todo maybe keep update frequency in check…
        this.valueOut = newValueOut;
    }

    valueOutChanged(newValue) {
        this.updateValid();
        this.updateDirty();
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
            this.valueChanged(this.value, null);
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
        this.valueChanged(this.value, null);
    }

    onPropertyValidUpdate = (value, binding) => {
        this.updateValid();
    };

    onSchemaValidUpdate = (value, binding) => {
        this.updateValid();
    };

    updateValid() {
        const typesToCheck = ["root", ...(this.containedTypes ?? [])];
        const childSchemasAreValid = typesToCheck.every(key => this.childSchemasValid[key]);

        const propKeys = this.extraProperties.map(prop => prop.propertyName);
        const allPropertiesValid = propKeys.every(key => {
            if (this.propertiesValid[key] != null) {
                return this.propertiesValid[key]; // property validity is known
            }
            // assume valid if not required and not present
            return !this.requiredProperties.has(key) && this.valueOut?.[key] === undefined;
        });
        if (!allPropertiesValid) {
            this.invalidProps = propKeys.filter(key => !this.propertiesValid[key]);
        } else {
            this.invalidProps = [];
        }

        let propertiesAreValid: boolean = false;
        if (this.requiredProperties == null || this.requiredProperties.size === 0) {
            propertiesAreValid = allPropertiesValid;
        } else {
            const requiredPropKeys = propKeys.filter(key => this.requiredProperties.has(key));
            const allRequiredPresent = this.requiredProperties.size === requiredPropKeys.length;
            propertiesAreValid = allPropertiesValid && allRequiredPresent;
        }

        if (this.valueOut == null) {
            this.valid = false; // this can never be nullable!
            return;
        }
        this.valid = propertiesAreValid && childSchemasAreValid;
    }

    onPropertyDirtyUpdate = (value, binding) => {
        this.updateDirty();
    };

    onSchemaDirtyUpdate = (value, binding) => {
        this.updateDirty();
    };

    updateDirty() {
        const typesToCheck = ["root", ...(this.containedTypes ?? [])];
        const childSchemasAreDirty = typesToCheck.some(key => this.childSchemasDirty[key]);

        let propertiesAreDirty = false;
        if (this.propertiesDirty != null) {
            const propKeys = this.extraProperties.map(prop => prop.propertyName);
            propertiesAreDirty = (propKeys.length === 0) || propKeys.some(key => this.propertiesDirty[key]);
        }

        this.dirty = propertiesAreDirty || childSchemasAreDirty;
    }
}
