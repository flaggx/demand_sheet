import {
  SERVICE_DAY_OPTIONS,
  SERVICE_FREQUENCY_OPTIONS,
  SERVICE_TECH_OPTIONS,
} from "@/lib/demand/service-options";

const selectCls =
  "mt-1 w-full rounded border border-neutral-700 bg-neutral-950 px-3 py-2 text-sm text-neutral-200";

type BaseProps = {
  id: string;
  defaultValue: string | null;
  /** Smaller padding for dense tables */
  compact?: boolean;
  /** If true, empty "—" is not submittable (native validation). */
  required?: boolean;
};

type OptionOverrideProps = {
  options?: readonly string[];
};

function buildAllowedSet(options: readonly string[]) {
  return new Set(options);
}

function ServiceEnumSelect({
  name,
  label,
  id,
  options,
  defaultValue,
  compact,
  required,
}: BaseProps & {
  name: string;
  label: string;
  options: readonly string[];
}) {
  const allowed = buildAllowedSet(options);
  const normalized =
    defaultValue == null || defaultValue === ""
      ? ""
      : String(defaultValue).trim();
  /** Stored value may not match the static list (e.g. real tech names). Show it as a normal option. */
  const storedOutsideList =
    normalized !== "" && !allowed.has(normalized) ? normalized : null;
  const cls = compact
    ? "mt-1 w-full rounded border border-neutral-700 bg-neutral-950 px-2 py-1.5 text-sm text-neutral-200"
    : selectCls;

  return (
    <div>
      <label htmlFor={id} className="text-xs text-neutral-500">
        {label}
      </label>
      <select
        id={id}
        name={name}
        defaultValue={normalized}
        required={required}
        className={cls}
      >
        <option value="">—</option>
        {storedOutsideList && (
          <option value={storedOutsideList}>{storedOutsideList}</option>
        )}
        {options.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
    </div>
  );
}

export function ServiceDaySelect(
  props: BaseProps & { id: string; label?: string } & OptionOverrideProps,
) {
  const { label: labelProp, options = SERVICE_DAY_OPTIONS, ...rest } = props;
  return (
    <ServiceEnumSelect
      {...rest}
      name="service_day"
      label={labelProp ?? "Service day"}
      options={options}
    />
  );
}

export function ServiceFrequencySelect(
  props: BaseProps & { id: string; label?: string } & OptionOverrideProps,
) {
  const { label: labelProp, options = SERVICE_FREQUENCY_OPTIONS, ...rest } = props;
  return (
    <ServiceEnumSelect
      {...rest}
      name="service_frequency"
      label={labelProp ?? "Frequency"}
      options={options}
    />
  );
}

export function ServiceTechSelect(
  props: BaseProps & { id: string; label?: string } & OptionOverrideProps,
) {
  const { label: labelProp, options = SERVICE_TECH_OPTIONS, ...rest } = props;
  return (
    <ServiceEnumSelect
      {...rest}
      name="service_tech"
      label={labelProp ?? "Tech"}
      options={options}
    />
  );
}
