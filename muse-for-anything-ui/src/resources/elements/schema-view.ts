import { bindable } from "aurelia-framework";
import { NormalizedApiSchema, NormalizedJsonSchema } from "rest/schema-objects";

export class SchemaView {
    @bindable data: any;
    @bindable schema: NormalizedApiSchema;

    schemaType: string;

    // eslint-disable-next-line complexity
    schemaChanged(newValue: NormalizedApiSchema, oldValue) {
        const normalized = newValue.normalized;
        if (normalized.enum != null) {
            this.schemaType = "enum";
        } else if (normalized.const != null) {
            this.schemaType = "const";
        } else if (normalized.mainType === "object") {
            this.schemaType = "object";
            // TODO type for mappings?
            if (normalized.customType != null) {
                if (normalized.customType === "resourceReference") {
                    this.schemaType = "resourceReference";
                }
                if (normalized.customType === "typeDefinition") {
                    this.schemaType = "typeDefinition";
                }
            }
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
            // FIXME type mappings in type definitions wont work because of oneOf…
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
