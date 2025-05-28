This is an explination of the regex used to break up the query string and group the attributes.

\.property\(

The literal string .property(.

The \. escapes the dot, meaning we match the actual period character.

\s*

Matches zero or more whitespace characters.

This allows for spaces after the parenthesis.

'([^']+)'

': Matches a single quote.

([^']+): A capturing group that matches one or more characters that are not a single quote.

This captures the key (or property name).

': Matches the closing single quote.

\s*,\s*

Matches a comma surrounded by optional whitespace.

(?:'([^']+)'|(-?\d+))

(?: ... ): A non-capturing group; it groups alternatives without creating a separate group number.

'([^']+)': One alternative that matches a string value:

It matches a single-quoted string and captures the content (the property value) in a group.

|: OR.

(-?\d+): The other alternative that matches a number:

-?: Optionally matches a minus sign for negative numbers.

\d+: Matches one or more digits.

This non-capturing group ensures we capture either a string (in group 2) or a number (in group 3).

\s*\)

Matches zero or more whitespace characters followed by a closing parenthesis.

