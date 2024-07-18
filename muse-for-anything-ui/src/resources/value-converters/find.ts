export class FindValueConverter {
    toView(value, element, comparator: "==" | "!=" | ">" | "<" | ">=" | "<=" = "==", defaultValue = undefined) {
        let found = undefined;
        if (value !== null && Array.isArray(value)) {
            if (comparator === "==") {
                found = value.find(v => v === element);
            } else if (comparator === "!=") {
                found = value.find(v => v !== element);
            } else if (comparator === "<") {
                found = value.find(v => v < element);
            } else if (comparator === ">") {
                found = value.find(v => v > element);
            } else if (comparator === "<=") {
                found = value.find(v => v <= element);
            } else if (comparator === ">=") {
                found = value.find(v => v >= element);
            }
        }
        if (found === undefined) {
            return defaultValue;
        }
        return found;
    }
}
