import { bindable } from "aurelia-framework";
import { NormalizedApiSchema, NormalizedJsonSchema } from "rest/schema-objects";

export class SchemaView {
    @bindable data: any;
    @bindable schema: NormalizedApiSchema;

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
            this.schemaType = this.getTypeForString(normalized);
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

    private getTypeForString(normalized: NormalizedJsonSchema): string {
        if (normalized.format != null) {
            return normalized.format;
        }
        if (normalized.contentMediaType != null) {
            // TODO
        }
        if (normalized.maxLength != null && normalized.maxLength < 300) {
            return "string";
        } else {
            return "text";
        }
    }
}
