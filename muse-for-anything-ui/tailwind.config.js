module.exports = {
    content: [
        './src/**/*.{html,js}',
    ],
    darkMode: 'class', // or 'media' or 'class'
    theme: {
        extend: {},
    },
    variants: {
        extend: {
            borderWidth: ['focus-within', 'focus'],
        },
    },
    plugins: [],
}
