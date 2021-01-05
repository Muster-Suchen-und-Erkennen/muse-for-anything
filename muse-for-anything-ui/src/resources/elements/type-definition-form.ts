import { bindable, bindingMode } from "aurelia-framework";
import { NormalizedApiSchema, PropertyDescription } from "rest/schema-objects";
import { SchemaValueObserver } from "./schema-value-observer";
import { nanoid } from "nanoid";

export class TypeDefinitionForm {
    @bindable key: string;
    @bindable label: string;
    @bindable initialData: any;
    @bindable schema: NormalizedApiSchema;
    @bindable required: boolean = false;
    @bindable debug: boolean = false;
    @bindable({ defaultBindingMode: bindingMode.fromView }) value: any;
    @bindable({ defaultBindingMode: bindingMode.fromView }) dirty: boolean = false;
    @bindable({ defaultBindingMode: bindingMode.fromView }) valid: boolean;

    slug = nanoid(8);

    choices: Array<{ title: string, description: string, schema: NormalizedApiSchema }> = [];
    chosenSchema: { title: string, description: string, schema: NormalizedApiSchema };

    typeValueObserver: SchemaValueObserver = {
        onValueChanged: (key, newValue, oldValue) => {
            //this.propChanged(key, newValue);
        },
        onValidityChanged: (key, newValue, oldValue) => {
            //this.propValidityChanged(key, newValue);
        },
    };

    initialDataChanged(newValue, oldValue) {

    }

    schemaChanged(newValue: NormalizedApiSchema, oldValue) {
        this.valid = false;
        const rawChoices = [...newValue.normalized.oneOf];
        const choices = rawChoices.map(schema => {
            const normalized = schema.normalized;
            if (normalized == null) {
                console.log(schema)
            }
            return {
                title: normalized.title ?? normalized.originRef,
                description: normalized.description ?? "",
                schema: schema,
            };
        });
        choices.sort((a, b) => {
            if (a.title > b.title) {
                return 1;
            }
            if (a.title < b.title) {
                return -1;
            }
            return 0;
        });
        this.choices = choices;
    }


    valueChanged(newValue, oldValue) {

    }
}
