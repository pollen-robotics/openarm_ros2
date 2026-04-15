cmake_minimum_required(VERSION 3.8)
project(openarm_gripette_description)

find_package(ament_cmake REQUIRED)

# Install URDF
install(DIRECTORY urdf
  DESTINATION share/${PROJECT_NAME}
)

# Install STL mesh files at the package share root so that
# package://openarm_gripette_description/<file>.stl resolves correctly
file(GLOB STL_FILES "*.stl")
install(FILES ${STL_FILES}
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
