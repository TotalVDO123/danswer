import { FiCheck, FiChevronDown } from "react-icons/fi";
import { CustomDropdown } from "../../Dropdown";

interface Option {
  key: string;
  display: string | JSX.Element;
  displayName?: string;
}
export function FilterDropdown({
  options,
  selected,
  handleSelect,
  icon,
  defaultDisplay,
  width = "w-64",
  dropdownWidth,
  optionClassName,
}: {
  options: Option[];
  selected: string[];
  handleSelect: (option: Option) => void;
  icon: JSX.Element;
  defaultDisplay: string | JSX.Element;
  width?: string;
  dropdownWidth?: string;
  optionClassName?: string;
}) {
  return (
    <div>
      <CustomDropdown
        dropdown={
          <div
            className={`
              border 
              border-border 
              rounded-lg 
              bg-background
              flex 
              flex-col 
              ${dropdownWidth || width}
              max-h-96 
              overflow-y-auto 
              overscroll-contain`}
          >
            {options.map((option, ind) => {
              const isSelected = selected.includes(option.key);
              return (
                <div
                  key={option.key}
                  className={`
                    ${optionClassName}
                    flex
                    px-3
                    text-sm
                    py-2.5
                    select-none
                    cursor-pointer
                    w-fit
                    text-emphasis
                    hover:bg-hover-light
                    ${
                      ind === options.length - 1 ? "" : "border-b border-border"
                    } 
                  `}
                  onClick={(event) => {
                    handleSelect(option);
                    event.preventDefault();
                    event.stopPropagation();
                  }}
                >
                  {option.display}
                  {isSelected && (
                    <div className="ml-auto mr-1">
                      <FiCheck />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        }
      >
        <div
          className={`
            flex
            ${width}
            text-sm
            px-3
            py-1.5
            rounded-lg 
            border 
            gap-x-2
            border-border
            cursor-pointer 
            hover:bg-hover-light`}
        >
          <div className="flex-none my-auto">{icon}</div>
          {selected.length === 0 ? (
            defaultDisplay
          ) : (
            <p className="line-clamp-1">{selected.join(", ")}</p>
          )}
          <FiChevronDown className="my-auto ml-auto" />
        </div>
      </CustomDropdown>
    </div>
  );
}
