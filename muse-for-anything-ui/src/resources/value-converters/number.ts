export class NumberValueConverter {
    toView(value, isInteger = false) {
        if (value == null) {
            return "";
        }
        return value.toString();
    }

    fromView(value, isInteger = false) {
        if (value == null || value === "") {
            return null;
        }
        if (isInteger) {
            return parseInt(value, 10);
        }
        return parseFloat(value);
    }
}
