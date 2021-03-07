import { bindable } from "aurelia-framework";
import { NormalizedApiSchema } from "rest/schema-objects";


export class TypeDefinitionView {
    @bindable data: any;
    @bindable schema: NormalizedApiSchema;

    metaSchema: NormalizedApiSchema;

    dataChanged(newValue, oldValue) {
        this.updateMetaSchema();
    }

    schemaChanged(newValue, oldValue) {
        this.updateMetaSchema();
    }

    // eslint-disable-next-line complexity
    updateMetaSchema() {
        if (this.schema == null) {
            return;
        }
        if (this.data == null) {
            return;
        }
        const choices = [...(this.schema.normalized.oneOf ?? [])];

        if (!(choices?.length > 0)) {
            return; // no choices to choose from
        }

        let schemaId: string;
        const initialType = this.data.type;
        if (initialType?.some(t => t === "object") ?? false) {
            schemaId = "#/definitions/object";
            const customObjectType = this.data.customType;
            // TODO use customObject type for object and taxonomy and type references!
            if (customObjectType === "resourceReference") {
                schemaId = "#/definitions/resourceReference";
            }
            if (this.data.$ref != null) {
                schemaId = "#/definitions/ref";
            }
        }
        if (initialType?.some(t => t === "array") ?? false) {
            schemaId = "#/definitions/array";
            if (this.data.arrayType === "tuple") {
                schemaId = "#/definitions/tuple";
            }
        } else if (initialType?.some(t => t === "string") ?? false) {
            schemaId = "#/definitions/string";
        } else if (initialType?.some(t => t === "number") ?? false) {
            schemaId = "#/definitions/number";
        } else if (initialType?.some(t => t === "integer") ?? false) {
            schemaId = "#/definitions/integer";
        } else if (initialType?.some(t => t === "boolean") ?? false) {
            schemaId = "#/definitions/boolean";
        } else if (this.data.enum != null) {
            schemaId = "#/definitions/enum";
        }

        this.metaSchema = choices.find(choice => {
            return choice.normalized.$id.endsWith(schemaId);
        });
    }
}
