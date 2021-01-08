import { bindable, bindingMode, autoinject } from "aurelia-framework";
import { NormalizedApiSchema, NormalizedJsonSchema } from "rest/schema-objects";
import { SchemaValueObserver } from "./schema-value-observer";

@autoinject
export class SchemaForm {
    @bindable key: string;
    @bindable label: string;
    @bindable initialData: any;
    @bindable schema: NormalizedApiSchema;
    @bindable required: boolean = false;
    @bindable valueObserver: SchemaValueObserver = null;
    @bindable debug: boolean = false;
    @bindable valuePush: any;
    @bindable({ defaultBindingMode: bindingMode.fromView }) value: unknown;
    @bindable({ defaultBindingMode: bindingMode.fromView }) valid: boolean;

    constructor(private element: Element) { }

    schemaType: string;
    extraType: string;

    // eslint-disable-next-line complexity
    schemaChanged(newValue: NormalizedApiSchema, oldValue) {
        const normalized = newValue.normalized;
        if (normalized.enum != null) {
            this.schemaType = "enum";
        } else if (normalized.const != null) {
            this.schemaType = "const";
            this.valid = true;
            this.value = normalized.const;
        } else if (normalized.mainType === "object") {
            if (normalized.customType != null) {
                this.extraType = normalized.customType;
                this.schemaType = "custom";
            } else {
                this.schemaType = "object";
                // TODO type for mappings?
            }
        } else if (normalized.mainType === "array") {
            this.schemaType = "array";
        } else if (normalized.mainType === "string") {
            this.schemaType = "string";
        } else if (normalized.mainType === "number") {
            this.schemaType = "number";
        } else if (normalized.mainType === "integer") {
            this.schemaType = "number";
        } else if (normalized.mainType === "boolean") {
            this.schemaType = "boolean";
        } else if (normalized.mainType === "null") {
            this.schemaType = "null";
        } else {
            this.schemaType = "unknown";
        }
    }

    valueObserverChanged(newObserver, oldObserver) {
        if (oldObserver == null) {
            return; // the first ever observer is set when value and etc. is not set yet
        }
        if (this.valueObserver?.onValueChanged != null) {
            this.valueObserver.onValueChanged(this.key, this.valuePush ?? this.value, undefined);
        }
        if (this.valueObserver?.onValidityChanged != null) {
            this.valueObserver.onValidityChanged(this.key, this.valid, undefined);
        }
    }

    valueChanged(newValue, oldValue) {
        if (this.valueObserver?.onValueChanged != null) {
            this.valueObserver.onValueChanged(this.key, newValue, oldValue);
        }
    }

    validChanged(newValue, oldValue) {
        if (this.valueObserver?.onValidityChanged != null) {
            this.valueObserver.onValidityChanged(this.key, newValue, oldValue);
        }
    }
}
