import { bindable, bindingMode, child } from "aurelia-framework";
import { NormalizedApiSchema, PropertyDescription } from "rest/schema-objects";
import { SchemaValueObserver } from "./schema-value-observer";


export class TypeRootForm {
    @bindable key: string;
    @bindable label: string;
    @bindable initialData: any;
    @bindable schema: NormalizedApiSchema;
    @bindable required: boolean = false;
    @bindable debug: boolean = false;
    @bindable valuePush: any;
    @bindable({ defaultBindingMode: bindingMode.fromView }) value: any;
    @bindable({ defaultBindingMode: bindingMode.fromView }) dirty: boolean = false;
    @bindable({ defaultBindingMode: bindingMode.fromView }) valid: boolean;

    typeSchema: NormalizedApiSchema;

    extraProperties: PropertyDescription[] = [];
    requiredProperties: Set<string> = new Set();

    invalidProps: Set<string> = new Set();
    validProps: Set<string> = new Set();

    containedTypes: string[] = [];

    propertyValueObserver: SchemaValueObserver = {
        onValueChanged: (key, newValue, oldValue) => {
            //this.propChanged(key, newValue);
        },
        onValidityChanged: (key, newValue, oldValue) => {
            //this.propValidityChanged(key, newValue);
        },
    };

    typeValueObserver: SchemaValueObserver = {
        onValueChanged: (key, newValue, oldValue) => {
            //this.propChanged(key, newValue);
        },
        onValidityChanged: (key, newValue, oldValue) => {
            //this.propValidityChanged(key, newValue);
        },
    };

    constructor() {
        this.value = {};
    }

    initialDataChanged(newValue, oldValue) {

    }

    schemaChanged(newValue: NormalizedApiSchema, oldValue) {
        this.invalidProps = new Set();
        this.validProps = new Set();
        this.valid = null;
        this.typeSchema = newValue.normalized.properties?.get("definitions")?.normalized?.additionalProperties as NormalizedApiSchema;
        this.reloadProperties();
    }

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
        this.extraProperties = this.schema.getPropertyList([], { // FIXME proper object keys...
            excludeReadOnly: true,
            blockList: ["$schema", "$ref", "definitions", "$comment", "title", "description", "deprecated", "allOf"],
        });
        const normalized = this.schema.normalized;
        this.requiredProperties = normalized.required;

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
        if (valueUpdate) {
            this.value = {
                ...this.value,
                ...valueUpdate,
            };
        }
    }

    valueChanged(newValue, oldValue) {
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
}
