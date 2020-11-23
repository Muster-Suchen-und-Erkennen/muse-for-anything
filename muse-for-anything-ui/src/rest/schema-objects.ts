import { error } from "console";
import { ApiObject, ApiResponse, isApiObject, isApiResponse } from "./api-objects";
import { SchemaService } from "./schema-service";

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
    hiddenProperties?: string[];
    propertyNames?: { pattern: string };
    propertyOrder?: { [prop: string]: number };
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
    contentMediaType?: string;
    contentEncoding?: "7bit" | "8bit" | "binary" | "quoted-printable" | "base64" | string;
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

export interface SchemaApiObject extends ApiObject {
    schema: JsonSchemaRoot;
}

export function isSchemaApiObject(obj: any): obj is SchemaApiObject {
    return isApiObject(obj) && (obj as any)?.schema != null;
}

export class ApiSchema {
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
        const originalRef = resolved.originRef;
        // if schema is reference then only resolve reference
        if (toResolve.$ref != null) {
            const nestedResolved = await this.resolveSchema(toResolve.$ref);
            // copy all keys over
            Object.assign(resolved, nestedResolved);
            if (originalRef != null) {
                resolved.originRef = originalRef;
            }
            return resolved;
        }
        // copy all keys over
        Object.assign(resolved, toResolve);
        // specifically resolve nested schemas
        await this.resolveGenericSchemaKeywords(toResolve, resolved);
        await this.resolveTypeSpecificSchemaKeywords(toResolve, resolved);
        if (originalRef != null) {
            resolved.originRef = originalRef;
        }
        return resolved;
    }

    public async resolveSchema(ref?: string): Promise<JsonSchema> {
        let toResolve: JsonSchema;
        // generate object instance here to avoid infinite recursions
        const resolved: JsonSchema = {
            // store a reference to the origin schema in the resolved schema
            originSchema: this,
            // store the original ref used to resolve this schema
            originRef: ref ?? "#",
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
            toResolve = this.schemaRoot.definitions?.[schemaName]; // TODO error/null checking
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

    public async getNormalizedApiSchema(ref?: string): Promise<NormalizedApiSchema> {
        const resolvedSchema = await this.resolveSchema(ref);
        return new NormalizedApiSchema(resolvedSchema);
    }
}

export interface NormalizedJsonSchema {
    $id?: string;
    type: Set<"object" | "array" | "string" | "number" | "integer" | "boolean" | "null">;
    mainType?: "object" | "array" | "string" | "number" | "integer" | "boolean" | "null";
    // valid everywhere
    enum?: Array<string | number | boolean | null>;
    const?: string | number | boolean | null;
    // generic/metadata attributes
    title?: string;
    description?: string;
    default?: any;
    examples?: any[];
    $comment?: string;
    // object attributes
    properties?: Map<string, NormalizedApiSchema>;
    propertiesAllowList?: Set<string>;
    patternProperties?: Map<RegExp, NormalizedApiSchema>;
    patternPropertiesAllowList?: string[][]; // for each array one pattern must match to allow name
    required?: Set<string>;
    additionalProperties?: boolean | NormalizedApiSchema;
    hiddenProperties?: Set<string>;
    propertyNames?: { pattern: RegExp[] };
    propertyOrder?: Map<string, number>;
    minProperties?: number;
    maxProperties?: number;
    dependencies?: { [prop: string]: string[] | { properties: { [prop: string]: NormalizedApiSchema }, required?: string[] } };
    // array attributes
    minItems?: number;
    maxItems?: number;
    uniqueItems?: boolean;
    items?: NormalizedApiSchema;
    tupleItems?: NormalizedApiSchema[];
    contains?: NormalizedApiSchema;
    additionalItems?: false | NormalizedApiSchema;
    // string attributes
    minLength?: number;
    maxLength?: number;
    pattern?: RegExp[];
    format?: string;
    contentMediaType?: string;
    contentEncoding?: "7bit" | "8bit" | "binary" | "quoted-printable" | "base64" | string;
    // numeric attributes
    multipleOf?: number[];
    minimum?: number;
    maximum?: number;
    exclusiveMinimum?: number;
    exclusiveMaximum?: number;
    [prop: string]: any;
}

const IGNORED_KEYS = new Set(["type"]);
const INCOMPATIBLE_KEYS = new Set(["$ref", "$anyOf", "$not", "$if", "$then", "$else", "dependencies"]);
const TYPE_SPECIFIC_KEYS = new Set([
    // object
    "properties",
    "patternProperties",
    "required",
    "additionalProperties",
    "propertyNames",
    "minProperties",
    "maxProperties",
    "dependencies",
    // array
    "minItems",
    "maxItems",
    "uniqueItems",
    "items",
    "tupleItems",
    "contains",
    "additionalItems",
    // string
    "minLength",
    "maxLength",
    "pattern",
    "format",
    "contentMediaType",
    "contentEncoding",
    // numbers
    "multipleOf",
    "minimum",
    "maximum",
    "exclusiveMinimum",
    "exclusiveMaximum",
]);


interface NormalizationContext {
    maxDepth: number;
    incompatibleKeys: Set<string>;
    properties?: Array<{ [prop: string]: JsonSchema }>;
    patternProperties?: Array<{ [prop: string]: JsonSchema }>;
    additionalProperties?: Array<JsonSchema | false>;
    items?: JsonSchema[];
    tupleItems?: JsonSchema[][];
    contains?: JsonSchema[];
    additionalItems?: Array<JsonSchema | false>;
}

const CONTEXT_COLLECT_KEYS = new Set(["properties", "patternProperties", "additionalProperties", "items", "tupleItems", "contains", "additionalItems"]);

function typeIsCompatible(typeSet: Set<string>, newType: string) {
    if (typeSet == null || typeSet.size === 0) {
        return true;
    }
    if (typeSet?.size >= 0) {
        return typeSet.has(newType);
    }
}

function mergeType(typeSet: Set<"object" | "array" | "string" | "number" | "integer" | "boolean" | "null">, newType: "object" | "array" | "string" | "number" | "integer" | "boolean" | "null" | Array<"object" | "array" | "string" | "number" | "integer" | "boolean" | "null">): Set<"object" | "array" | "string" | "number" | "integer" | "boolean" | "null"> {
    if (typeof newType === "string") {
        if (typeIsCompatible(typeSet, newType)) {
            return new Set([newType]);
        }
    } else {
        if (newType.every(nType => typeIsCompatible(typeSet, nType))) {
            return new Set([...newType]);
        }
    }
    throw Error(`The type ${newType} is not compatible with the already defined type ${typeSet}`);
}

function mergeMinProperty(key, normalized: NormalizedJsonSchema, toNormalize: JsonSchema) {
    if (normalized[key] != null) {
        if (normalized[key] < toNormalize[key]) {
            // new value is more restrictive
            normalized[key] = toNormalize[key];
        }
    } else {
        normalized[key] = toNormalize[key];
    }
    return;
}

function mergeMaxProperty(key, normalized: NormalizedJsonSchema, toNormalize: JsonSchema) {
    if (normalized[key] != null) {
        if (normalized[key] > toNormalize[key]) {
            // new value is more restrictive
            normalized[key] = toNormalize[key];
        }
    } else {
        normalized[key] = toNormalize[key];
    }
    return;
}

// eslint-disable-next-line complexity
function mergeObjectProperties(key, normalized: NormalizedJsonSchema, toNormalize: ObjectJsonSchema) {
    // type of toNormalize is not enforced here!
    if (key === "required") {
        const req = normalized.required ?? new Set<string>();
        toNormalize.required.forEach(r => req.add(r));
        normalized.required = req;
        return;
    }
    if (key === "propertyNames" && toNormalize.propertyNames?.pattern != null) {
        const propNames = normalized.propertyNames ?? { pattern: [] };
        propNames.pattern.push(RegExp(toNormalize.propertyNames.pattern));
        normalized.propertyNames = propNames;
        return;
    }
    if (key === "minProperties") {
        mergeMinProperty(key, normalized, toNormalize);
        return;
    }
    if (key === "maxProperties") {
        mergeMaxProperty(key, normalized, toNormalize);
        return;
    }
    if (key === "propertyOrder") {
        const orderMap = normalized.propertyOrder ?? new Map<string, number>();
        Object.keys(toNormalize.propertyOrder).forEach(propName => {
            orderMap.set(propName, toNormalize.propertyOrder[propName]);
        });
        normalized.propertyOrder = orderMap;
        return;
    }
    if (key === "hiddenProperties") {
        const hidden = normalized.hiddenProperties ?? new Set<string>();
        toNormalize.hiddenProperties.forEach(r => hidden.add(r));
        normalized.hiddenProperties = hidden;
        return;
    }
}

function mergeArrayProperties(key, normalized: NormalizedJsonSchema, toNormalize: ArrayBaseJsonSchema) {
    if (key === "minItems") {
        mergeMinProperty(key, normalized, toNormalize);
        return;
    }
    if (key === "maxItems") {
        mergeMaxProperty(key, normalized, toNormalize);
        return;
    }
    if (key === "uniqueItems") {
        normalized.uniqueItems = toNormalize.uniqueItems || Boolean(normalized.uniqueItems);
    }
}

function mergeStringProperties(key, normalized: NormalizedJsonSchema, toNormalize: StringJsonSchema) {
    if (key === "minLength") {
        mergeMinProperty(key, normalized, toNormalize);
        return;
    }
    if (key === "maxLength") {
        mergeMaxProperty(key, normalized, toNormalize);
        return;
    }
    if (key === "pattern") {
        const patterns = normalized.pattern ?? [];
        patterns.push(RegExp(toNormalize.pattern));
        normalized.pattern = patterns;
        return;
    }
    if (key === "format" || key === "contentMediaType" || key === "contentEncoding") {
        if (normalized[key] == null) {
            normalized[key] = toNormalize[key];
            return;
        }
        if (normalized[key] !== toNormalize[key]) {
            throw Error(`Ìncompatible string types. Attribute ${key} has incompatible values "${normalized[key]}" "${toNormalize[key]}"!`);
        }
        // properties match, nothing to do.
        return;
    }
}

// eslint-disable-next-line complexity
function mergeNumericProperties(key, normalized: NormalizedJsonSchema, toNormalize: NumericJsonSchema) {
    if (key === "multipleOf") {
        const multiples = normalized.multipleOf ?? [];
        multiples.push(toNormalize.multipleOf);
        normalized.multipleOf = multiples;
        return;
    }
    if (key === "minimum") {
        if (normalized.exclusiveMinimum == null) {
            mergeMinProperty(key, normalized, toNormalize);
            return;
        }
        if (normalized.exclusiveMinimum < toNormalize.minimum) {
            normalized.exclusiveMinimum = null;
            normalized.minimum = toNormalize.minimum;
        }
        return;
    }
    if (key === "exclusiveMinimum") {
        if (normalized.minimum == null) {
            mergeMinProperty(key, normalized, toNormalize);
            return;
        }
        if (normalized.minimum <= toNormalize.exclusiveMinimum) {
            normalized.minimum = null;
            normalized.exclusiveMinimum = toNormalize.exclusiveMinimum;
        }
        return;
    }
    if (key === "maximum") {
        if (normalized.exclusiveMaximum == null) {
            mergeMaxProperty(key, normalized, toNormalize);
            return;
        }
        if (normalized.exclusiveMaximum > toNormalize.maximum) {
            normalized.exclusiveMaximum = null;
            normalized.maximum = toNormalize.maximum;
        }
        return;
    }
    if (key === "exclusiveMaximum") {
        if (normalized.maximum == null) {
            mergeMaxProperty(key, normalized, toNormalize);
            return;
        }
        if (normalized.maximum >= toNormalize.exclusiveMaximum) {
            normalized.maximum = null;
            normalized.exclusiveMaximum = toNormalize.exclusiveMaximum;
        }
        return;
    }
}

function mergeProperties(key, normalized: NormalizedJsonSchema, toNormalize: JsonSchema) {
    if (key === "enum") {
        if (normalized.enum == null || toNormalize.enum.every(entry => normalized.enum.includes(entry))) {
            normalized.enum = [...toNormalize.enum];
            return;
        }
        throw Error(`Incompatible enums ${toNormalize.enum} must be part of ${normalized.enum}!`);
    }
    if (key === "const") {
        // use enum first and later normalize one entry enums back to consts
        if (normalized.enum == null || normalized.enum.includes(toNormalize.const)) {
            normalized.enum = [toNormalize.const];
            return;
        }
        throw Error(`Incompatible const ${toNormalize.const} must be part of ${normalized.enum}!`);
    }
    mergeObjectProperties(key, normalized, toNormalize as ObjectJsonSchema);
    mergeArrayProperties(key, normalized, toNormalize as ArrayBaseJsonSchema);
    mergeStringProperties(key, normalized, toNormalize as StringJsonSchema);
    mergeNumericProperties(key, normalized, toNormalize as NumericJsonSchema);
}


function consolidatePropertiesLike(propertiesLists: Array<{ [prop: string]: JsonSchema }>): Map<string, NormalizedApiSchema> {
    const newProps: Map<string, NormalizedApiSchema> = new Map();
    const tempMap: Map<string, JsonSchema[]> = new Map();

    // merge schemas into lists at property level
    propertiesLists.forEach(props => {
        Object.keys(props).forEach(propName => {
            const schemas = tempMap.get(propName) ?? [];
            schemas.push(props[propName]);
            tempMap.set(propName, schemas);
        });
    });

    // use lists of schemas to generate new NormalizedApiSchema schemas
    tempMap.forEach((schemas, propName) => {
        if (schemas.length === 0) {
            newProps.set(propName, new NormalizedApiSchema({}));
            return;
        }
        if (schemas.length === 1) {
            newProps.set(propName, new NormalizedApiSchema(schemas[0]));
            return;
        }
        newProps.set(propName, new NormalizedApiSchema({ $allOf: schemas }));
    });

    return newProps;
}

function consolidateSchemaList(schemas: Array<JsonSchema | false>, allowFalse = false): NormalizedApiSchema | false {
    if (schemas.includes(false)) {
        if (allowFalse) {
            // if any schema says no additional properties allowed then hope that the
            // merged properties are honoring that restriction (they currently do with the allowLists)
            return false;
        } else {
            throw Error("Encountered `false` instead of a schema!");
        }
    }
    // schemas cannot contain false below this line
    if (schemas.length === 0) {
        return new NormalizedApiSchema({});
    }
    if (schemas.length === 1) {
        return new NormalizedApiSchema((schemas as JsonSchema[])[0]);
    }
    return new NormalizedApiSchema({ $allOf: (schemas as JsonSchema[]) });
}


function consolidateObjectProperties(normalized: NormalizedJsonSchema, context: NormalizationContext) {
    if (context.properties != null) {
        normalized.properties = consolidatePropertiesLike(context.properties);
    }
    if (context.patternProperties != null) {
        const patternProps = consolidatePropertiesLike(context.patternProperties);
        const patternProperties = new Map<RegExp, NormalizedApiSchema>();
        patternProps.forEach((schema, pattern) => patternProperties.set(RegExp(pattern), schema));
        normalized.patternProperties = patternProperties;
    }
    if (context.additionalProperties) {
        normalized.additionalProperties = consolidateSchemaList(context.additionalProperties, true);
    }
    if (normalized.additionalProperties == null) {
        // normalize this to default to `true`
        normalized.additionalProperties = true;
    }
}

function consolidateArrayProperties(normalized: NormalizedJsonSchema, context: NormalizationContext) {
    if (context.contains != null) {
        normalized.contains = consolidateSchemaList(context.contains) as NormalizedApiSchema;
    }
    if (context.items != null) {
        normalized.items = consolidateSchemaList(context.items) as NormalizedApiSchema;
    }
    if (context.tupleItems != null) {
        const extraSchemas = context.items ?? []; // include any additional items schema into tuple items validation
        const tupleItemsTemp: JsonSchema[][] = [];
        // merge schemas into lists for each index
        context.tupleItems.forEach(tupleSchemas => {
            tupleSchemas.forEach((schema, index) => {
                if (index >= tupleItemsTemp.length) {
                    // first entry in a list includes extra schemas
                    tupleItemsTemp.push([...extraSchemas, schema]);
                    return;
                }
                tupleItemsTemp[index].push(schema);
            });
        });
        // build new tupleItems
        normalized.tupleItems = tupleItemsTemp.map(schemas => consolidateSchemaList(schemas) as NormalizedApiSchema);
    }
    if (context.additionalItems != null) {
        const extraSchemas = context.items ?? []; // include any additional items schema into additional items validation
        normalized.additionalItems = consolidateSchemaList([...extraSchemas, ...context.additionalItems], true);
    }
}


export interface PropertyDescription {
    propertyName: string;
    propertySchema: NormalizedApiSchema;
    isPatternProperty: boolean;
    isAdditionalProperty: boolean;
    sortKey: number;
}

export class NormalizedApiSchema {

    private resolvedSchema: JsonSchema;
    private normalizedSchema: NormalizedJsonSchema;

    constructor(resolvedJsonSchema: JsonSchema) {
        this.resolvedSchema = resolvedJsonSchema;
    }

    public get normalized(): NormalizedJsonSchema {
        if (this.normalizedSchema != null) {
            return this.normalizedSchema;
        }
        const normalized: NormalizedJsonSchema = { type: null };
        const context: NormalizationContext = {
            maxDepth: 20,
            incompatibleKeys: new Set(),
        };
        this.normalizeSchema(normalized, this.resolvedSchema, context, context.maxDepth);
        this.consolidateWithContext(normalized, context);
        this.normalizedSchema = normalized;
        return normalized;
    }

    public getPropertyList(obj?: any, options: { includeHidden?: boolean, allowList?: Iterable<string>, blockList?: Iterable<string> } = { blockList: ["self"] }): PropertyDescription[] {
        if (!this.normalized.type.has("object")) {
            throw Error("Cannot read properties of a non object schema!");
        }

        const blockList = new Set<string>(options.blockList ?? []);
        if (!options.includeHidden && this.normalized.hiddenProperties != null) {
            this.normalized.hiddenProperties.forEach(propName => blockList.add(propName));
        }
        const hasAllowList = options.allowList != null;
        const allowList = hasAllowList ? new Set<string>(options.allowList) : null;

        const props: PropertyDescription[] = [];
        const knownProps = new Set<string>();

        const propOrder = this.normalized.propertyOrder;
        const properties = this.normalized.properties;
        if (properties != null) {
            properties.forEach((propSchema, propName) => {
                knownProps.add(propName);
                if (hasAllowList && !allowList.has(propName)) {
                    return; // not in allow list, skip
                }
                if (!hasAllowList && blockList.has(propName)) {
                    // allowList dominates blocklist completely
                    return; // in block list, skip
                }
                props.push({
                    propertyName: propName,
                    propertySchema: propSchema,
                    isAdditionalProperty: false,
                    isPatternProperty: false,
                    sortKey: propOrder?.get(propName) ?? 10,
                });
            });
        }
        if (obj == null) {
            // cannot determine pattern or additional properties without an object
            return props.sort((a, b) => a.sortKey - b.sortKey);
        }
        const patternProperties = this.normalized.patternProperties;
        const additionalProperties = this.normalized.additionalProperties ?? true;
        let additionalSchema: NormalizedApiSchema;
        if (additionalProperties === false) {
            additionalSchema = null;
        } else if (additionalProperties === true) {
            additionalSchema = new NormalizedApiSchema({});
        } else {
            additionalSchema = additionalProperties;
        }

        Object.keys(obj).forEach(propName => {
            if (knownProps.has(propName)) {
                return; // defined in properties, no need to recheck
            }
            if (hasAllowList && !allowList.has(propName)) {
                return; // not in allow list, skip
            }
            if (!hasAllowList && blockList.has(propName)) {
                // allowList dominates blocklist completely
                return; // in block list, skip
            }
            let foundKey = false;
            if (patternProperties != null) {
                patternProperties.forEach((schema, pattern) => {
                    if (foundKey) {
                        return; // fast exit
                    }
                    if (pattern.test(propName)) {
                        foundKey = true;
                        props.push({
                            propertyName: propName,
                            propertySchema: schema,
                            isAdditionalProperty: false,
                            isPatternProperty: true,
                            sortKey: propOrder?.get(propName) ?? propOrder?.get(pattern.source) ?? 1000,
                        });
                    }
                });
            }
            if (additionalProperties !== false && !foundKey) {
                props.push({
                    propertyName: propName,
                    propertySchema: additionalSchema,
                    isAdditionalProperty: false,
                    isPatternProperty: true,
                    sortKey: propOrder?.get(propName) ?? 100000,
                });
            }
        });

        return props.sort((a, b) => a.sortKey - b.sortKey);
    }

    // eslint-disable-next-line complexity
    private normalizeSchema(normalized: NormalizedJsonSchema, toNormalize: JsonSchema, context: NormalizationContext, maxDepth: number): void {
        if (toNormalize == null || !toNormalize) {
            return;
        }
        if (maxDepth < 0) {
            console.warn(`Schema was nested too deep with inheritance ($allOf) and not all constraints will be applied correctly! Maximum allowed depth is ${context.maxDepth}!`, normalized);
        }

        // check all of before all other keys
        if (toNormalize.$allOf != null) {
            // apply allOf inheritance in the correct order
            toNormalize.$allOf.forEach(schema => this.normalizeSchema(normalized, schema, context, maxDepth - 1));
        }
        // check type before other keys
        if (toNormalize.type != null) {
            try {
                normalized.type = mergeType(normalized.type, toNormalize.type);
            } catch (error) {
                console.warn(`Cannot merge schemas with incompatible types ${normalized.type} ${toNormalize.type}!`);
                // TODO add error to context
                return;
            }
        }

        // check other keys
        Object.keys(toNormalize).forEach(key => {
            if (IGNORED_KEYS.has(key)) {
                return;
            }
            if (INCOMPATIBLE_KEYS.has(key)) {
                context.incompatibleKeys.add(key);
                return;
            }
            if (CONTEXT_COLLECT_KEYS.has(key)) {
                // first collect all applying schemas into lists to be merged later
                if (key === "items") {
                    // special handling for tuple items
                    if (Array.isArray(toNormalize[key])) {
                        const schemas = context.tupleItems ?? [];
                        schemas.push(toNormalize[key]);
                        context.tupleItems = schemas;
                        return;
                    }
                }
                const schemas = context[key] ?? [];
                schemas.push(toNormalize[key]);
                context[key] = schemas;
                return;
            }
            mergeProperties(key, normalized, toNormalize);
        });

        // check if additional properties are forbidden
        if (toNormalize.additionalProperties === false) {
            // update propertiesAllowList
            const propNames = Object.keys((toNormalize as ObjectJsonSchema).properties ?? {});
            if (normalized.propertiesAllowList != null) {
                const propNameSet = new Set<string>();
                propNames.forEach(propName => {
                    if (normalized.propertiesAllowList.has(propName)) {
                        propNameSet.add(propName);
                        return;
                    }
                    if (normalized.patternPropertiesAllowList == null) {
                        // only check if no extra patterns allowed
                        if (normalized.required.has(propName)) {
                            throw Error(`Schema can never be valid as property ${propName} is required but not in the list of allowed properties!`);
                        }
                    }
                });
                normalized.propertiesAllowList = propNameSet;
            } else {
                normalized.propertiesAllowList = new Set(propNames);
            }
            // update patternPropertiesAllowList
            if (toNormalize.patternProperties != null) {
                const patternPropNames = Object.keys((toNormalize as ObjectJsonSchema).patternProperties);
                const patternPropAllowList = normalized.patternPropertiesAllowList ?? [];
                patternPropAllowList.push(patternPropNames);
                normalized.patternPropertiesAllowList = patternPropAllowList;
            }
        }
    }

    // eslint-disable-next-line complexity
    private consolidateWithContext(normalized: NormalizedJsonSchema, context: NormalizationContext): void {
        if (normalized.enum != null) {
            if (normalized.enum.length === 1) {
                normalized.const = normalized.enum[0];
                normalized.enum = null;
            }
            return; // always assume that enums/const values are ok without extra validation
        }
        if (normalized.type == null || normalized.type.size === 0) {
            const isEnumOrConst = Object.keys(normalized).some(key => key === "enum" || key === "const");
            const normalizedHasTypeSpecificKeys = Object.keys(normalized).some(key => TYPE_SPECIFIC_KEYS.has(key));
            const contextHasTypeSpecificKeys = Object.keys(context).some(key => TYPE_SPECIFIC_KEYS.has(key));
            if (!isEnumOrConst && (normalizedHasTypeSpecificKeys || contextHasTypeSpecificKeys)) {
                // has type specific keywords but
                throw Error("Schema cannot be normalized as it has no given type!");
            }
        }
        if (normalized.type.has("object")) {
            normalized.mainType = "object";
            consolidateObjectProperties(normalized, context);
            return;
        }
        if (normalized.type.has("array")) {
            normalized.mainType = "array";
            consolidateArrayProperties(normalized, context);
            return;
        }
        if (normalized.type.has("string")) {
            normalized.mainType = "string";
            return;
        }
        if (normalized.type.has("number")) {
            normalized.mainType = "number";
            return;
        }
        if (normalized.type.has("integer")) {
            normalized.mainType = "integer";
            return;
        }
        if (normalized.type.has("boolean")) {
            normalized.mainType = "boolean";
            return;
        }
        if (normalized.type.has("null")) {
            normalized.mainType = "null";
            // only null allowed for this type
            normalized.const = null;
            return;
        }
    }
}
