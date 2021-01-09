import { bindable, bindingMode, autoinject } from "aurelia-framework";
import { NormalizedApiSchema, NormalizedJsonSchema } from "rest/schema-objects";

export type UpdateSignal = () => void;

@autoinject
export class SchemaForm {
    @bindable key: string;
    @bindable label: string;
    @bindable initialData: any;
    @bindable schema: NormalizedApiSchema;
    @bindable required: boolean = false;
    @bindable debug: boolean = false;
    @bindable noCard: boolean = false;
    @bindable valuePush: any;
    @bindable updateSignal: UpdateSignal;
    @bindable({ defaultBindingMode: bindingMode.twoWay }) value: unknown;
    @bindable({ defaultBindingMode: bindingMode.fromView }) valid: boolean;
    @bindable({ defaultBindingMode: bindingMode.fromView }) dirty: boolean;

    constructor(private element: Element) { }

    activeSchema: NormalizedApiSchema;
    schemaType: string;
    extraType: string;

    constValue: any;

    // eslint-disable-next-line complexity
    schemaChanged(newValue: NormalizedApiSchema, oldValue) {
        this.constValue = undefined;
        this.activeSchema = null;
        const normalized = newValue.normalized;
        if (normalized.enum != null) {
            this.schemaType = "enum";
        } else if (normalized.const != null) {
            this.schemaType = "const";
            this.valid = true;
            this.constValue = normalized.const;
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
        this.activeSchema = newValue;
    }

    valueChanged(newValue, oldValue) {
        if (this.constValue !== undefined && newValue !== this.constValue) {
            this.valid = true;
            this.value = this.constValue;
        }
    }

    validChanged(newVal, oldVal) {
        if (this.updateSignal != null) {
            this.updateSignal();
        }
    }

    dirtyChanged(newVal, oldVal) {
        if (this.updateSignal != null) {
            this.updateSignal();
        }
    }
}
