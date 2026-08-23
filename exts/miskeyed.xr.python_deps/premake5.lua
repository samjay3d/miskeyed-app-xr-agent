local ext = get_current_extension_info()

project_ext(ext)

repo_build.prebuild_link {
    { "../../../_build/target-deps/pip_prebundle", ext.target_dir.."/pip_prebundle" },
}

