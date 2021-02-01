import { bindable, observable, bindingMode } from "aurelia-framework";
import { NormalizedApiSchema, PropertyDescription } from "rest/schema-objects";
import { nanoid } from "nanoid";

interface SchemaDescription {
    title: string;
    description: string;
    schema: NormalizedApiSchema;
}

export class TypeDefinitionForm {
    @bindable key: string;
    @bindable label: string;
    @bindable initialData: any;
    @bindable schema: NormalizedApiSchema;
    @bindable required: boolean = false;
    @bindable debug: boolean = false;
    @bindable valuePush: any;
    @bindable actions: Iterable<string>;
    @bindable actionSignal: unknown;
    @bindable({ defaultBindingMode: bindingMode.twoWay }) value: any;
    @bindable({ defaultBindingMode: bindingMode.fromView }) dirty: boolean;
    @bindable({ defaultBindingMode: bindingMode.fromView }) valid: boolean;

    slug = nanoid(8);

    choices: SchemaDescription[] = [];
    @observable() chosenSchema: SchemaDescription;

    activeSchema: SchemaDescription;

    valueCache: Map<string, any> = new Map();

    childValid: boolean;

    initialDataChanged(newValue, oldValue) {
        this.updateChoiceFromInitialData(true);
    }

    // eslint-disable-next-line complexity
    updateChoiceFromInitialData(forceUpdate: boolean = false) {
        if (!(this.choices?.length > 0)) {
            return; // no choices to choose from
        }
        if (!this.initialData) {
            return; // no initial data to update from
        }
        if (this.chosenSchema != null && !forceUpdate) {
            return; // some schema already chosen
        }
        let schemaId: string;
        const initialType = this.initialData.type;
        if (initialType.some(t => t === "object")) {
            schemaId = "#/definitions/object";
            const customObjectType = this.initialData.customType;
            // TODO use customObject type for object and taxonomy and type references!
            if (this.initialData.$ref != null) {
                schemaId = "#/definitions/ref";
            }
        }
        if (initialType.some(t => t === "array")) {
            schemaId = "#/definitions/array";
            if (this.initialData.arrayType === "tuple") {
                schemaId = "#/definitions/tuple";
            }
        } else if (initialType.some(t => t === "string")) {
            schemaId = "#/definitions/string";
        } else if (initialType.some(t => t === "number")) {
            schemaId = "#/definitions/number";
        } else if (initialType.some(t => t === "integer")) {
            schemaId = "#/definitions/integer";
        } else if (initialType.some(t => t === "boolean")) {
            schemaId = "#/definitions/boolean";
        } else if (this.initialData.enum != null) {
            schemaId = "#/definitions/enum";
        }

        const choice = this.choices.find(choice => {
            return choice.schema.normalized.$id.endsWith(schemaId);
        });
        if (choice != null) {
            window.setTimeout(() => {
                if (this.value == null) {
                    this.value = {};
                }
                this.activeSchema = choice;
                this.chosenSchema = choice;
            }, 0);
        }
    }

    schemaChanged(newValue: NormalizedApiSchema, oldValue) {
        if (newValue == null) {
            return;
        }
        if (newValue.normalized.customType !== "typeDefinition") {
            return;
        }
        if (newValue.normalized.oneOf == null) {
            console.warn(this.key, this.slug, newValue, this)
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
        this.updateChoiceFromInitialData();

        window.setTimeout(() => {
            this.updateValid();
        }, 0);
    }


    valueChanged(newValue, oldValue) {
        this.updateValid();
    }

    childValidChanged() {
        this.updateValid();
    }

    updateValid() {
        if (this.value == null) {
            this.valid = false; // this object type is never nullable
        } else {
            this.valid = this.childValid ?? false;
        }
    }

    chosenSchemaChanged(newSchemaValue: SchemaDescription, oldSchemaValue: SchemaDescription) {
        if (this.activeSchema === newSchemaValue) {
            return; // change is from code to ui
        }
        const oldValue = this.value ?? {};
        if (oldSchemaValue != null) {
            this.valueCache.set(oldSchemaValue.title, oldValue);
        }
        this.value = {};
        this.activeSchema = null; // always set active schema to null first to reset child form
        if (newSchemaValue == null) {
            this.value = null;
            return;
        }
        const newValue: any = {};
        if (newSchemaValue.schema.normalized.default != null) {
            const defaultValue = newSchemaValue.schema.normalized.default;
            Object.assign(newValue, JSON.parse(JSON.stringify(defaultValue)));
        }
        if (this.valueCache.has(newSchemaValue.title)) {
            const cachedValue = this.valueCache.get(newSchemaValue.title);
            console.log(JSON.stringify(newValue), cachedValue, Object.keys(cachedValue))
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

        // use timeout so that aurelia bindings resgister the reset before setting the new values!
        window.setTimeout(() => {
            this.activeSchema = newSchemaValue;

            this.value = newValue;
        }, 0);
    }
}
