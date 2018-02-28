// takes enabled modules from the environment variable
const AETHER_MODULES = (process.env.AETHER_MODULES || '').split(',')
export const ODK_ACTIVE = (AETHER_MODULES.indexOf('odk') > -1)

// these are used to export the responses as a CSV file using the CustomCSVRenderer
export const CSV_HEADER_RULES = process.env.CSV_HEADER_RULES || ''
export const CSV_HEADER_RULES_SEP = process.env.CSV_HEADER_RULES_SEP || ':'
