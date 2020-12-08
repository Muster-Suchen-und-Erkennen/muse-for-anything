import { bindable, bindingMode, autoinject } from "aurelia-framework";
import { NormalizedApiSchema, NormalizedJsonSchema } from "rest/schema-objects";

@autoinject
export class SchemaForm {
    @bindable label: string;
    @bindable initialData: any;
    @bindable schema: NormalizedApiSchema;
    @bindable required: boolean = false;
    @bindable({ defaultBindingMode: bindingMode.fromView }) value: string;
    @bindable({ defaultBindingMode: bindingMode.fromView }) valid: boolean;

    constructor(private element: Element) { }

    schemaType: string;

    schemaChanged(newValue: NormalizedApiSchema, oldValue) {
        const normalized = newValue.normalized;
        if (normalized.enum != null) {
            this.schemaType = "enum";
        } else if (normalized.const != null) {
            this.schemaType = "const";
        } else if (normalized.mainType === "object") {
            this.schemaType = "object";
            // TODO type for mappings?
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

    valueChanged(newValue, oldValue) {
        const event = new CustomEvent<{ newValue: any, oldValue: any }>("change", {
            detail: { newValue, oldValue },
            cancelable: false,
            bubbles: true,
        });
        this.element.dispatchEvent(event);
    }

    validChanged(newValue, oldValue) {
        const event = new CustomEvent<{ newValue: any, oldValue: any }>("valid-change", {
            detail: { newValue, oldValue },
            cancelable: false,
            bubbles: true,
        });
        this.element.dispatchEvent(event);
    }
}
