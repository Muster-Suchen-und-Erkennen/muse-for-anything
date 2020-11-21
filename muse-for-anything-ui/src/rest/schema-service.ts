import { autoinject } from "aurelia-framework";
import { ApiObject, ApiResponse, isApiObject, isApiResponse } from "./api-objects";
import { BaseApiService } from "./base-api";

interface JsonSchema {
    $id?: string;
    type?: "object" | "array" | "string" | "number" | "integer" | "boolean" | "null" | Array<"object" | "array" | "string" | "number" | "integer" | "boolean" | "null">;
    // combining schemas
    $ref?: string;
    $allOf?: JsonSchema[];
    $anyOf?: JsonSchema[];
    $oneOf?: JsonSchema[];
    $not?: JsonSchema;
    // if
    $if?: JsonSchema;
    $then?: JsonSchema;
    $else?: JsonSchema;
    // valid everywhere
    enum?: Array<string | number | boolean | null>;
    const?: string | number | boolean | null;
    // generic/metadata attributes
    title?: string;
    description?: string;
    default?: any;
    examples?: any[];
    $comment?: string;
    [prop: string]: any;
}

interface ObjectJsonSchema extends JsonSchema {
    type: "object" | Array<"object" | "null">;
    properties?: { [prop: string]: JsonSchema };
    patternProperties?: { [prop: string]: JsonSchema };
    required?: string[];
    additionalProperties?: boolean | JsonSchema;
    propertyNames?: { pattern: string };
    minProperties?: number;
    maxProperties?: number;
    dependencies?: { [prop: string]: string[] | { properties: { [prop: string]: JsonSchema }, required?: string[] } };
}

function isObjectJsonSchema(obj: any): obj is ObjectJsonSchema {
    return obj?.properties != null || obj?.required != null || obj?.patternProperties != null || obj?.additionalProperties != null || obj?.propertyNames != null;
}

interface ArrayBaseJsonSchema extends JsonSchema {
    type: "array" | Array<"array" | "null">;
    minItems?: number;
    maxItems?: number;
    uniqueItems?: boolean;
    contentMediaType?: string;
    contentEncoding?: "7bit" | "8bit" | "binary" | "quoted-printable" | "base64" | string;
}

interface ArrayJsonSchema extends ArrayBaseJsonSchema {
    items?: JsonSchema;
    contains?: JsonSchema;
}

function isArrayJsonSchema(obj: any): obj is ArrayJsonSchema {
    return !isTupleJsonSchema(obj) && (obj?.items != null || obj?.contains != null);
}

interface TupleJsonSchema extends ArrayBaseJsonSchema {
    items: JsonSchema[];
    additionalItems?: boolean | JsonSchema;
}

function isTupleJsonSchema(obj: any): obj is TupleJsonSchema {
    return obj?.items != null && Array.isArray(obj.items);
}

interface StringJsonSchema extends JsonSchema {
    type: "string" | Array<"string" | "null">;
    minLength?: number;
    maxLength?: number;
    pattern?: string;
    format?: string;
}

interface NumericJsonSchema extends JsonSchema {
    type: "number" | "integer" | Array<"number" | "integer" | "null">;
    multipleOf?: number;
    minimum?: number;
    maximum?: number;
    exclusiveMinimum?: number;
    exclusiveMaximum?: number;
}

interface JsonSchemaRoot extends JsonSchema {
    $schema: string;
    // schema structuring
    definitions?: { [prop: string]: JsonSchema };
}

function isJsonSchemaRoot(obj: any): obj is JsonSchemaRoot {
    return obj?.$schema != null;
}

interface SchemaApiObject extends ApiObject {
    schema: JsonSchemaRoot;
}

function isSchemaApiObject(obj: any): obj is SchemaApiObject {
    return isApiObject(obj) && (obj as any)?.schema != null;
}

class ApiSchema {
    private schemaService: SchemaService;
    private apiResponse?: ApiResponse<SchemaApiObject>;
    private schemaRoot: JsonSchemaRoot;

    private resolvedRoot: JsonSchema;
    private resolvedSchemas: Map<string, JsonSchema> = new Map();

    constructor(schema: ApiResponse<SchemaApiObject> | JsonSchemaRoot, schemaService: SchemaService) {
        this.schemaService = schemaService;
        if (isApiResponse(schema)) {
            if (!isSchemaApiObject(schema.data)) {
                throw Error(`Unsupported ApiResponse wrapper for a schema! ${schema.data}`);
            }
            this.apiResponse = schema;
            this.schemaRoot = schema.data.schema;
        }
    }

    private async resolveGenericSchemaKeywords(toResolve: JsonSchema, resolved: JsonSchema) {
        if (toResolve.$allOf != null) {
            resolved.$allOf = [];
            const promises = [];
            toResolve.$allOf.forEach(innerSchema => {
                const resolvedInnerSchema = this.resolveSchemaInstance(innerSchema);
                promises.push(resolvedInnerSchema);
            });
            const results = await Promise.all(promises);
            results.forEach(res => resolved.$allOf.push(res));
        }
        if (toResolve.$anyOf != null) {
            resolved.$anyOf = [];
            const promises = [];
            toResolve.$anyOf.forEach(innerSchema => {
                const resolvedInnerSchema = this.resolveSchemaInstance(innerSchema);
                promises.push(resolvedInnerSchema);
            });
            const results = await Promise.all(promises);
            results.forEach(res => resolved.$anyOf.push(res));
        }
        if (toResolve.$oneOf != null) {
            resolved.$oneOf = [];
            const promises = [];
            toResolve.$oneOf.forEach(innerSchema => {
                const resolvedInnerSchema = this.resolveSchemaInstance(innerSchema);
                promises.push(resolvedInnerSchema);
            });
            const results = await Promise.all(promises);
            results.forEach(res => resolved.$oneOf.push(res));
        }
        if (toResolve.$not != null) {
            resolved.$not = await this.resolveSchemaInstance(toResolve.$not);
        }
        if (toResolve.$if != null) {
            resolved.$if = await this.resolveSchemaInstance(toResolve.$if);
        }
        if (toResolve.$then != null) {
            resolved.$then = await this.resolveSchemaInstance(toResolve.$then);
        }
        if (toResolve.$else != null) {
            resolved.$else = await this.resolveSchemaInstance(toResolve.$else);
        }
    }

    private async resolveTypeSpecificSchemaKeywords(toResolve: JsonSchema, resolved: JsonSchema) {
        if (isArrayJsonSchema(toResolve)) {
            resolved.items = await this.resolveSchemaInstance(toResolve.items);
        }
        if (isTupleJsonSchema(toResolve)) {
            resolved.items = [];
            const promises = [];
            toResolve.items.forEach(innerSchema => {
                const resolvedInnerSchema = this.resolveSchemaInstance(innerSchema);
                promises.push(resolvedInnerSchema);
            });
            const results = await Promise.all(promises);
            results.forEach(res => resolved.items.push(res));
            if (toResolve.additionalItems != null && typeof toResolve.additionalItems !== "boolean") {
                resolved.additionalItems = await this.resolveSchemaInstance(toResolve.additionalItems);
            }
        }
        if (isObjectJsonSchema(toResolve)) {
            if (toResolve.properties != null) {
                resolved.properties = {};
                const promises = Object.keys(toResolve.properties).map(async key => {
                    const innerSchema = toResolve.properties[key];
                    resolved.properties[key] = await this.resolveSchemaInstance(innerSchema);
                });
                await Promise.all(promises);
            }
            if (toResolve.patternProperties != null) {
                resolved.patternProperties = {};
                const promises = Object.keys(toResolve.patternProperties).map(async key => {
                    const innerSchema = toResolve.patternProperties[key];
                    resolved.patternProperties[key] = await this.resolveSchemaInstance(innerSchema);
                });
                await Promise.all(promises);
            }
            if (toResolve.additionalProperties != null && typeof toResolve.additionalProperties !== "boolean") {
                resolved.additionalProperties = await this.resolveSchemaInstance(toResolve.additionalProperties);
            }
        }
    }

    private async resolveSchemaInstance(toResolve: JsonSchema, resolvedSchema?: JsonSchema): Promise<JsonSchema> {
        const resolved: JsonSchema = resolvedSchema ?? {};
        if (toResolve == null) {
            return resolved; // empty schema
        }
        // if schema is reference then only resolve reference
        if (toResolve.$ref != null) {
            return this.resolveSchema(toResolve.$ref);
        }
        // copy all keys over
        Object.assign(resolved, toResolve);
        // specifically resolve nested schemas
        await this.resolveGenericSchemaKeywords(toResolve, resolved);
        await this.resolveTypeSpecificSchemaKeywords(toResolve, resolved);
        return resolved;
    }

    public async resolveSchema(ref?: string): Promise<JsonSchema> {
        let toResolve: JsonSchema;
        // generate object instance here to avoid infinite recursions
        const resolved: JsonSchema = {
            // store a reference to the origin schema in the resolved schema
            originSchema: this,
            // store the original ref used to resolve this schema
            originRef: ref,
        };
        if (ref == null || ref === "") {
            if (this.resolvedRoot != null) {
                // already finished (or at least started resolving)
                return this.resolvedRoot;
            }
            toResolve = this.schemaRoot;
            // store object to get resolved before resolving to avoid infinite recursions
            this.resolvedRoot = resolved;
        } else if (ref.startsWith("#/definitions/")) {
            if (this.resolvedSchemas.has(ref)) {
                // already finished (or at least started resolving)
                return this.resolvedSchemas.get(ref);
            }
            const schemaName = ref.substring(14);
            toResolve = this.schemaRoot.definitions?.[schemaName];
            // store object to get resolved before resolving to avoid infinite recursions
            this.resolvedSchemas.set(ref, resolved);
        } else {
            // ref does not point to the root or a contained schema
            const schema = await this.schemaService.getSchema(ref);
            const fragment = this.schemaService.getSchemaFragmentFromUrl(ref);
            return await schema.resolveSchema(fragment);
        }
        return await this.resolveSchemaInstance(toResolve, resolved);
    }
}

@autoinject
export class SchemaService {

    private schemaMap: Map<string, ApiSchema> = new Map();

    private api: BaseApiService;

    constructor(baseApi: BaseApiService) {
        this.api = baseApi;
    }

    public getSchemaFragmentFromUrl(ref: string): string {
        if (ref == null || ref === "") {
            return null;
        }
        const fragmentIndex = ref.indexOf("#");
        if (fragmentIndex < 0) {
            return null;
        }
        return ref.substring(fragmentIndex);
    }

    public getUrlWithoutFragment(ref: string): string {
        const fragmentIndex = ref.indexOf("#");
        if (fragmentIndex < 0) {
            return ref;
        }
        return ref.substring(0, fragmentIndex);
    }

    public async getSchema(ref: string): Promise<ApiSchema> {
        const href = this.getUrlWithoutFragment(ref);
        if (this.schemaMap.has(href)) {
            return this.schemaMap.get(href);
        }
        const schemaResponse = await this.api.fetch<ApiResponse<SchemaApiObject>>(href);
        const schema = new ApiSchema(schemaResponse, this);
        if (!this.schemaMap.has(href)) {
            // only store the first schema instance (fetch could be long running)
            this.schemaMap.set(href, schema);
        }
        return this.schemaMap.get(href);
    }
}
