local ext = get_current_extension_info()

project_ext(ext)

repo_build.prebuild_link {
    { "config", ext.target_dir.."/config" },
    { "miskeyed", ext.target_dir.."/miskeyed" },
}

