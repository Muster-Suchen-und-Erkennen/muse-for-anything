import { autoinject } from "aurelia-framework";
import { ApiObject, ApiResponse, isApiObject, isApiResponse } from "./api-objects";
import { BaseApiService } from "./base-api";
import { ApiSchema, SchemaApiObject } from "./schema-objects";

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
        const schemaResponse = await this.api.fetch<ApiResponse<SchemaApiObject>>(href, undefined, true); // FIXME true for cache busting
        const schema = new ApiSchema(schemaResponse, this);
        if (!this.schemaMap.has(href)) {
            // only store the first schema instance (fetch could be long running)
            this.schemaMap.set(href, schema);
        }
        return this.schemaMap.get(href);
    }
}
