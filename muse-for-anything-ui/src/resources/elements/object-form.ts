import { bindable, bindingMode, children, child, observable } from "aurelia-framework";
import { NormalizedApiSchema, PropertyDescription } from "rest/schema-objects";

export class ObjectForm {
    @bindable label: string;
    @bindable initialData: any;
    @bindable schema: NormalizedApiSchema;
    @bindable({ defaultBindingMode: bindingMode.fromView }) value: any = {};
    @bindable({ defaultBindingMode: bindingMode.fromView }) valid: boolean;

    properties: PropertyDescription[] = [];
    required: Set<string> = new Set();

    invalidProps: Set<string> = new Set();
    validProps: Set<string> = new Set();

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

    propChanged(propertyName, event) {
        if (event.detail == null) {
            return;
        }
        this.value = {
            ...this.value,
            [propertyName]: event.detail?.newValue,
        };
    }

    propValidityChanged(propertyName, event) {
        if (event.detail == null) {
            return;
        }
        if (event.detail.newValue) {
            this.invalidProps.delete(propertyName);
            this.validProps.add(propertyName);
        } else {
            this.invalidProps.add(propertyName);
            this.validProps.delete(propertyName);
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
