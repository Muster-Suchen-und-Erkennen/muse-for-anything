import { bindable } from "aurelia-framework";
import { nanoid } from "nanoid";
import { NormalizedApiSchema } from "rest/schema-objects";

export class NewPropertyInfo {
    @bindable schema?: NormalizedApiSchema;

    slug = nanoid(8);
}
