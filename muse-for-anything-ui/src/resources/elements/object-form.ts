import { bindable, bindingMode, children, child, observable } from "aurelia-framework";
import { NormalizedApiSchema, PropertyDescription } from "rest/schema-objects";
import { SchemaValueObserver } from "./schema-value-observer";

export class ObjectForm {
    @bindable key: string;
    @bindable label: string;
    @bindable initialData: any;
    @bindable schema: NormalizedApiSchema;
    @bindable debug: boolean = false;
    @bindable valuePush: any;
    @bindable({ defaultBindingMode: bindingMode.fromView }) value: any = {};
    @bindable({ defaultBindingMode: bindingMode.fromView }) valid: boolean;

    properties: PropertyDescription[] = [];
    propertiesByKey: Map<string, PropertyDescription> = new Map();
    required: Set<string> = new Set();

    invalidProps: Set<string> = new Set();
    validProps: Set<string> = new Set();

    valueObserver: SchemaValueObserver = {
        onValueChanged: (key, newValue, oldValue) => {
            this.propChanged(key as string, newValue);
        },
        onValidityChanged: (key, newValue, oldValue) => {
            this.propValidityChanged(key as string, newValue);
        },
    };

    initialDataChanged(newValue, oldValue) {
        this.reloadProperties();
    }

    valuePushChanged(newValue, oldValue) {
        if (this.value === newValue) {
            return;
        }
        this.value = newValue;
    }

    schemaChanged(newValue, oldValue) {
        this.invalidProps = new Set();
        this.validProps = new Set();
        this.valid = null;
        this.reloadProperties();
    }

    reloadProperties() {
        if (this.schema == null) {
            this.properties = [];
            this.required = new Set();
            return;
        }
        if (!this.schema.normalized.type.has("object")) {
            console.error("Not an object!"); // FIXME better error!
            this.properties = [];
            this.required = new Set();
            return;
        }
        const currentData = { // TODO refactor to be less costly (maybe use set?)
            ...this.initialData,
            ...(this.value ?? {}),
        };
        const properties = this.schema.getPropertyList(Object.keys(currentData));
        const propertiesByKey = new Map<string, PropertyDescription>();
        properties.forEach(prop => propertiesByKey.set(prop.propertyName, prop));
        this.properties = properties;
        this.propertiesByKey = propertiesByKey;
        this.required = this.schema.normalized.required;
    }

    propChanged(key: string, newValue) {
        if (this.value[key] === newValue) {
            return;
        }
        if (!this.required.has(key) && newValue == null) {
            // if key is not required then remove it if value is null
            if (this.value[key] !== undefined) {
                // only remove it if key is present in the object
                const temp = {
                    ...this.value,
                };
                delete temp[key];
                this.value = temp;
                return;
            }
        }
        if (this.value[key] == null && newValue == null) {
            return;
        }
        this.value = {
            ...this.value,
            [key]: newValue,
        };
    }

    propValidityChanged(key: string, newValue) {
        if (newValue) {
            this.invalidProps.delete(key);
            this.validProps.add(key);
        } else {
            this.invalidProps.add(key);
            this.validProps.delete(key);
        }
        const knownProps = this.invalidProps.size + this.validProps.size;
        if (knownProps < this.properties.length) {
            // valid status not known for all props
            this.valid = (this.invalidProps.size > 0) ? true : null;
        } else {
            this.valid = this.invalidProps.size === 0;
        }
    }
}
