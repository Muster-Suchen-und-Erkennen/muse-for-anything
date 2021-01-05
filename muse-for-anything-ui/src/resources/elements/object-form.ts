import { bindable, bindingMode, children, child, observable } from "aurelia-framework";
import { NormalizedApiSchema, PropertyDescription } from "rest/schema-objects";
import { SchemaValueObserver } from "./schema-value-observer";

export class ObjectForm {
    @bindable key: string;
    @bindable label: string;
    @bindable initialData: any;
    @bindable schema: NormalizedApiSchema;
    @bindable debug: boolean = false;
    @bindable({ defaultBindingMode: bindingMode.fromView }) value: any = {};
    @bindable({ defaultBindingMode: bindingMode.fromView }) valid: boolean;

    properties: PropertyDescription[] = [];
    required: Set<string> = new Set();

    invalidProps: Set<string> = new Set();
    validProps: Set<string> = new Set();

    valueObserver: SchemaValueObserver = {
        onValueChanged: (key, newValue, oldValue) => {
            this.propChanged(key, newValue);
        },
        onValidityChanged: (key, newValue, oldValue) => {
            this.propValidityChanged(key, newValue);
        },
    };

    initialDataChanged(newValue, oldValue) {
        this.reloadProperties();
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
        this.properties = this.schema.getPropertyList(this.initialData);
        this.required = this.schema.normalized.required;
    }

    propChanged(key: string, newValue) {
        if (this.value[key] === newValue) {
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
