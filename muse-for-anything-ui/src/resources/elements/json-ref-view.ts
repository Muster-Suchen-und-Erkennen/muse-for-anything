import { autoinject, bindable } from "aurelia-framework";
import { ApiLink, ApiObject } from "rest/api-objects";
import { BaseApiService } from "rest/base-api";
import { NormalizedApiSchema } from "rest/schema-objects";
import { SchemaService } from "rest/schema-service";


@autoinject()
export class JsonRefView {
    @bindable data: any;
    @bindable schema: NormalizedApiSchema;
    @bindable context: any;

    contextOut: any;

    base: string | null = null;
    ref: string | null = null;

    baseApiLink: ApiLink | null = null;
    refTitle: string | null = null;

    private apiService: BaseApiService;
    private schemas: SchemaService;

    constructor(rest: BaseApiService, schemas: SchemaService) {
        this.apiService = rest;
        this.schemas = schemas;
    }


    dataChanged(newValue, oldValue) {
        const ref = newValue?.$ref ?? null;
        const value = this.splitUrl(ref);
        this.base = value.base;
        this.ref = value.ref;

        if (this.base != null) {
            this.updateBaseApiLink();
        }
        this.updateRefTitle();
    }

    contextChanged(newValue, oldValue) {
        this.updateRefTitle();
    }

    private splitUrl(value: string | null) {
        if (value == null) {
            return { base: null, ref: null };
        }

        const split = value.split("#", 2);
        const base = split[0] ? split[0] : null;

        if (split.length === 1) {
            return { base: base, ref: null };
        }
        const fragment = split[1];

        if (fragment.startsWith("/definitions/")) {
            return { base: base, ref: fragment.substring(13) };
        }

        return { base: base, ref: null };
    }

    private async updateBaseApiLink() {
        if (this.base == null) {
            this.baseApiLink = null;
            return;
        }
        if (this.base === this.baseApiLink?.href) {
            return;  // nothing to update
        }
        try {
            const response = await this.apiService.getByApiLink<ApiObject>({
                href: this.base,
                resourceType: "ont-type-version",
                rel: [],
            }, false);
            if (response?.data?.self?.resourceType === "ont-type-version") {
                this.baseApiLink = response?.data?.self ?? null;
            }
        } catch {
            // do not update
        }
    }

    private async updateRefTitle() {
        if (this.ref == null) {
            this.refTitle == null;
            return;
        }
        if (this.base) {
            const baseSchema = await this.schemas.getSchema(this.base);
            const typeDef = baseSchema.getDefinedTypes().find(typeDef => typeDef.key === this.ref);
            // eslint-disable-next-line no-ternary
            this.refTitle = typeDef?.title ? `${typeDef?.title} (${typeDef?.key})` : null;
            return;
        }
        const typeDef = (this.context?.topLevelTypeDefs ?? []).find(def => def.key === this.ref);
        // eslint-disable-next-line no-ternary
        this.refTitle = typeDef?.title ? `${typeDef?.title} (${typeDef?.key})` : null;
    }

}
