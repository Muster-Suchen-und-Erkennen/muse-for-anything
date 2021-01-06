import { bindable, observable, bindingMode } from "aurelia-framework";
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
    @bindable valuePush: any;
    @bindable({ defaultBindingMode: bindingMode.fromView }) value: any;
    @bindable({ defaultBindingMode: bindingMode.fromView }) dirty: boolean = false;
    @bindable({ defaultBindingMode: bindingMode.fromView }) valid: boolean;

    slug = nanoid(8);

    choices: Array<{ title: string, description: string, schema: NormalizedApiSchema }> = [];
    @observable() chosenSchema: { title: string, description: string, schema: NormalizedApiSchema };

    valueCache: Map<string, any> = new Map();

    typeValueObserver: SchemaValueObserver = {
        onValueChanged: (key, newValue, oldValue) => {
            //this.propChanged(key, newValue);
            this.value = newValue;
        },
        onValidityChanged: (key, newValue, oldValue) => {
            //this.propValidityChanged(key, newValue);
            this.valid = newValue;
        },
    };

    initialDataChanged(newValue, oldValue) {

    }

    schemaChanged(newValue: NormalizedApiSchema, oldValue) {
        this.valid = false;
        if (newValue == null) {
            return;
        }
        if (newValue.normalized.oneOf == null) {
            console.warn(newValue)
        }
        const rawChoices = [...(newValue.normalized.oneOf ?? [])];
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

    chosenSchemaChanged(newSchemaValue, oldSchemaValue) {
        const oldValue = this.value ?? {};
        if (oldSchemaValue != null) {
            this.valueCache.set(oldSchemaValue.title, oldValue);
        }
        if (newSchemaValue == null) {
            return;
        }
        console.log(newSchemaValue)
        const newValue: any = {};
        if (newSchemaValue.schema.normalized.default != null) {
            const defaultValue = newSchemaValue.schema.normalized.default;
            Object.assign(newValue, JSON.parse(JSON.stringify(defaultValue)));
        }
        if (this.valueCache.has(newSchemaValue.title)) {
            const cachedValue = this.valueCache.get(newSchemaValue.title);
            Object.keys(cachedValue).forEach(key => {
                if (cachedValue[key] != null) {
                    newValue[key] = cachedValue[key];
                }
            });
        }
        ["title", "description", "$comment", "deprecated"].forEach(attr => {
            if (oldValue[attr] != null) {
                newValue[attr] = oldValue[attr];
            }
        });
        this.valuePush = newValue;
    }
}
